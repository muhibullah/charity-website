from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from unfold.admin import ModelAdmin

from .models import FAQ, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    fieldsets = (
        ("Home page", {"fields": ("announcement", "tagline", "intro", "hero_image")}),
        ("About page", {"fields": ("about_text",)}),
        ("Contact", {"fields": ("contact_email", "whatsapp_link")}),
        ("Bank details (shown on the Donate page)", {
            "fields": ("bank_account_name", "bank_sort_code", "bank_account_number", "bank_reference_hint"),
        }),
    )

    def changelist_view(self, request, extra_context=None):
        # There is only one settings row, so skip the list and open it directly.
        obj = SiteSettings.load()
        return redirect(reverse("admin:website_sitesettings_change", args=[obj.pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FAQ)
class FAQAdmin(ModelAdmin):
    list_display = ("question", "order", "is_published")
    list_editable = ("order", "is_published")
    search_fields = ("question", "answer")
