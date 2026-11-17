from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.db.models import OuterRef, Subquery, Sum
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .admin_utils import RecordedByMixin, export_as_csv_action
from .models import Donation, Donor, MonthlyPlan

STATUS_COLOURS = {
    "Completed": "success",
    "Active": "success",
    "Pending": "warning",
    "Paused": "warning",
    "Failed": "danger",
    "Refunded": "danger",
    "Cancelled": "danger",
}


class MonthlyPlanInline(TabularInline):
    model = MonthlyPlan
    extra = 0
    fields = ("amount", "method", "day_of_month", "status", "started_on")


class DonationInline(TabularInline):
    model = Donation
    fk_name = "donor"
    extra = 0
    fields = ("received_on", "amount", "method", "kind", "status", "reference")
    ordering = ("-received_on",)
    show_change_link = True


@admin.register(Donor)
class DonorAdmin(ModelAdmin):
    list_display = ("__str__", "phone", "email", "source", "monthly_amount", "total_given", "is_active", "joined_on")
    list_filter = ("source", "is_active", "show_name_publicly")
    search_fields = ("first_name", "last_name", "email", "phone")
    inlines = [MonthlyPlanInline, DonationInline]
    readonly_fields = ("stripe_customer_id", "created_at")
    fieldsets = (
        (None, {"fields": ("first_name", "last_name", "email", "phone")}),
        ("Membership", {"fields": ("source", "joined_on", "is_active", "show_name_publicly")}),
        ("Private", {"fields": ("notes", "stripe_customer_id", "created_at")}),
    )
    actions = [
        export_as_csv_action([
            ("first_name", "First name"), ("last_name", "Last name"), ("email", "Email"),
            ("phone", "Phone"), ("get_source_display", "Source"), ("joined_on", "Joined"),
            ("is_active", "Active"),
        ])
    ]

    def get_queryset(self, request):
        # Subqueries (not plain joins) so donations and plans don't multiply each other's totals.
        def total_of(queryset):
            return Subquery(queryset.filter(donor=OuterRef("pk")).values("donor").annotate(t=Sum("amount")).values("t"))

        return super().get_queryset(request).annotate(
            _total_given=total_of(Donation.objects.filter(status=Donation.Status.COMPLETED)),
            _monthly=total_of(MonthlyPlan.objects.filter(status=MonthlyPlan.Status.ACTIVE)),
        )

    @display(description="Monthly", ordering="_monthly")
    def monthly_amount(self, obj):
        return f"£{obj._monthly:,.2f}" if obj._monthly else "-"

    @display(description="Total given", ordering="_total_given")
    def total_given(self, obj):
        return f"£{obj._total_given or 0:,.2f}"


@admin.register(MonthlyPlan)
class MonthlyPlanAdmin(ModelAdmin):
    list_display = ("donor", "amount_display", "method", "day_of_month", "status_badge", "started_on")
    list_filter = ("status", "method")
    search_fields = ("donor__first_name", "donor__last_name", "donor__email")
    autocomplete_fields = ("donor",)
    readonly_fields = ("stripe_subscription_id",)

    @display(description="Amount", ordering="amount")
    def amount_display(self, obj):
        return f"£{obj.amount:,.2f}"

    @display(description="Status", label=STATUS_COLOURS)
    def status_badge(self, obj):
        return obj.get_status_display()


@admin.register(Donation)
class DonationAdmin(RecordedByMixin, ModelAdmin):
    list_display = ("received_on", "donor_name", "amount_display", "method", "kind", "status_badge", "reference")
    list_filter = ("status", "method", "kind", "received_on")
    search_fields = ("donor__first_name", "donor__last_name", "donor__email", "reference")
    date_hierarchy = "received_on"
    autocomplete_fields = ("donor", "monthly_plan")
    readonly_fields = ("stripe_payment_id", "recorded_by", "created_at")
    fieldsets = (
        (None, {"fields": ("donor", "monthly_plan", "amount", "received_on")}),
        ("Payment", {"fields": ("method", "kind", "status", "reference")}),
        ("Other", {"fields": ("notes", "stripe_payment_id", "recorded_by", "created_at")}),
    )
    actions = [
        export_as_csv_action([
            ("received_on", "Date"), ("donor", "Donor"), ("amount", "Amount (£)"),
            ("get_method_display", "Method"), ("get_kind_display", "Type"),
            ("get_status_display", "Status"), ("reference", "Reference"),
        ])
    ]

    @display(description="Donor", ordering="donor__first_name")
    def donor_name(self, obj):
        return obj.donor or "Anonymous"

    @display(description="Amount", ordering="amount")
    def amount_display(self, obj):
        return f"£{obj.amount:,.2f}"

    @display(description="Status", label=STATUS_COLOURS)
    def status_badge(self, obj):
        return obj.get_status_display()


# Re-register Django's built-in users and groups so they use the Unfold look too.
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
