from django.conf import settings
from django.db import models
from django.utils import timezone

from donations.models import POSITIVE_AMOUNT


class Recipient(models.Model):
    """A person or family the group helps. Private details never appear on the public website."""

    reference = models.CharField(max_length=20, unique=True, editable=False)
    display_name = models.CharField(
        max_length=100, help_text="Public name used on the website, e.g. a first name or 'A family in Leeds'."
    )
    full_name = models.CharField(max_length=200, blank=True, help_text="Private.")
    phone = models.CharField(max_length=30, blank=True, help_text="Private.")
    location = models.CharField(max_length=150, blank=True, help_text="Town / city / country.")
    household_size = models.PositiveSmallIntegerField(null=True, blank=True)
    situation = models.TextField(blank=True, help_text="Private notes about their circumstances.")
    consent_to_publish = models.BooleanField(
        default=False, help_text="They agreed that their story (with display name) may appear on the website."
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} - {self.display_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.reference:
            # R-0001, R-0002 ... based on the database id, so it never repeats.
            self.reference = f"R-{self.pk:04d}"
            super().save(update_fields=["reference"])


class Payout(models.Model):
    """Money (or goods) given to a recipient."""

    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        BANK = "bank", "Bank transfer"
        MOBILE = "mobile", "Mobile money"
        GOODS = "goods", "Goods (food parcel, etc.)"

    class Purpose(models.TextChoices):
        FOOD = "food", "Food"
        RENT = "rent", "Rent / housing"
        BILLS = "bills", "Bills"
        MEDICAL = "medical", "Medical"
        EDUCATION = "education", "Education"
        OTHER = "other", "Other"

    recipient = models.ForeignKey(Recipient, on_delete=models.PROTECT, related_name="payouts")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=POSITIVE_AMOUNT)
    paid_on = models.DateField(default=timezone.localdate)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.BANK)
    purpose = models.CharField(max_length=20, choices=Purpose.choices, default=Purpose.FOOD)
    notes = models.TextField(blank=True)
    proof = models.FileField(upload_to="payout-proofs/%Y/%m/", blank=True, help_text="Receipt or photo (private).")
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_on", "-created_at"]

    def __str__(self):
        return f"£{self.amount} to {self.recipient.display_name} on {self.paid_on:%d %b %Y}"
