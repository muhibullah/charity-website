import csv

from django.http import HttpResponse
from django.utils import timezone


def export_as_csv_action(fields, description="Export selected to CSV (Excel)"):
    """Admin action: download the selected rows as a CSV file that opens in Excel."""

    def export_as_csv(modeladmin, request, queryset):
        model_name = modeladmin.model._meta.verbose_name_plural.replace(" ", "-")
        filename = f"{model_name}-{timezone.localdate():%Y-%m-%d}.csv"
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow([label for _, label in fields])
        for obj in queryset:
            row = []
            for attr, _ in fields:
                value = obj
                for part in attr.split("__"):
                    value = getattr(value, part, "") if value is not None else ""
                    if callable(value):
                        value = value()
                row.append("" if value is None else value)
            writer.writerow(row)
        return response

    export_as_csv.short_description = description
    return export_as_csv


class RecordedByMixin:
    """Remember which admin user typed in the record."""

    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, "recorded_by_id") and not obj.recorded_by_id:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)
