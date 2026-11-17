from django.contrib import admin
from django.db.models import Count, Sum
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from donations.admin_utils import RecordedByMixin, export_as_csv_action

from .models import Payout, Recipient


class PayoutInline(TabularInline):
    model = Payout
    extra = 0
    fields = ("paid_on", "amount", "method", "purpose", "notes")
    ordering = ("-paid_on",)


@admin.register(Recipient)
class RecipientAdmin(ModelAdmin):
    list_display = ("reference", "display_name", "location", "household_size", "total_received", "times_helped",
                    "consent_to_publish", "is_active")
    list_filter = ("is_active", "consent_to_publish")
    search_fields = ("reference", "display_name", "full_name", "location", "phone")
    readonly_fields = ("reference", "created_at")
    inlines = [PayoutInline]
    fieldsets = (
        ("Public", {"fields": ("reference", "display_name", "location", "consent_to_publish")}),
        ("Private", {"fields": ("full_name", "phone", "household_size", "situation", "is_active", "created_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_total=Sum("payouts__amount"), _count=Count("payouts"))

    @display(description="Total received", ordering="_total")
    def total_received(self, obj):
        return f"£{obj._total or 0:,.2f}"

    @display(description="Times helped", ordering="_count")
    def times_helped(self, obj):
        return obj._count


@admin.register(Payout)
class PayoutAdmin(RecordedByMixin, ModelAdmin):
    list_display = ("paid_on", "recipient", "amount_display", "method", "purpose", "recorded_by")
    list_filter = ("purpose", "method", "paid_on")
    search_fields = ("recipient__reference", "recipient__display_name", "recipient__full_name", "notes")
    date_hierarchy = "paid_on"
    autocomplete_fields = ("recipient",)
    readonly_fields = ("recorded_by", "created_at")
    actions = [
        export_as_csv_action([
            ("paid_on", "Date"), ("recipient__reference", "Recipient ref"),
            ("recipient__display_name", "Recipient"), ("amount", "Amount (£)"),
            ("get_method_display", "Method"), ("get_purpose_display", "Purpose"), ("notes", "Notes"),
        ])
    ]

    @display(description="Amount", ordering="amount")
    def amount_display(self, obj):
        return f"£{obj.amount:,.2f}"
