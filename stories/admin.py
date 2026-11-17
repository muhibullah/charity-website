from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import Story


@admin.register(Story)
class StoryAdmin(ModelAdmin):
    list_display = ("title", "published_badge", "published_on", "recipient")
    list_filter = ("is_published",)
    search_fields = ("title", "summary", "body")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("recipient",)
    actions = ["publish", "unpublish"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "recipient":
            kwargs["queryset"] = db_field.related_model.objects.filter(consent_to_publish=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @display(description="Status", label={"Published": "success", "Draft": "warning"})
    def published_badge(self, obj):
        return "Published" if obj.is_published else "Draft"

    @admin.action(description="Publish selected stories")
    def publish(self, request, queryset):
        queryset.update(is_published=True)

    @admin.action(description="Unpublish selected stories")
    def unpublish(self, request, queryset):
        queryset.update(is_published=False)
