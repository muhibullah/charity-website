from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

POSITIVE_AMOUNT = [MinValueValidator(Decimal("0.01"))]


class Donor(models.Model):
    """A person who gives money - an existing WhatsApp member or someone who joined via the website."""

    class Source(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp group"
        WEBSITE = "website", "Website"
        OTHER = "other", "Other"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.WHATSAPP)
    show_name_publicly = models.BooleanField(
        default=False, help_text="If unticked, this donor is shown as 'Anonymous' on the website."
    )
    is_active = models.BooleanField(default=True)
    joined_on = models.DateField(default=timezone.localdate)
    stripe_customer_id = models.CharField(max_length=100, blank=True, editable=False)
    notes = models.TextField(blank=True, help_text="Private - only visible to admins.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def public_name(self):
        return str(self) if self.show_name_publicly else "Anonymous"


class MonthlyPlan(models.Model):
    """A donor's regular monthly commitment, e.g. £10 every month."""

    class Method(models.TextChoices):
        STRIPE = "stripe", "Card (Stripe)"
        STANDING_ORDER = "standing_order", "Bank standing order"
        MANUAL = "manual", "Cash / manual transfer"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        CANCELLED = "cancelled", "Cancelled"

    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name="monthly_plans")
    amount = models.DecimalField(max_digits=8, decimal_places=2, validators=POSITIVE_AMOUNT)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.STANDING_ORDER)
    day_of_month = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text="Usual payment day (1-28), if known.",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    started_on = models.DateField(default=timezone.localdate)
    cancelled_on = models.DateField(null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_on"]

    def __str__(self):
        return f"{self.donor} - £{self.amount}/month ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if self.status == self.Status.CANCELLED and not self.cancelled_on:
            self.cancelled_on = timezone.localdate()
        super().save(*args, **kwargs)


class Donation(models.Model):
    """A single payment received (one-off, or one month of a monthly plan)."""

    class Method(models.TextChoices):
        STRIPE = "stripe", "Card (Stripe)"
        BANK = "bank", "Bank transfer"
        CASH = "cash", "Cash"
        OTHER = "other", "Other"

    class Kind(models.TextChoices):
        ONE_OFF = "one_off", "One-off"
        MONTHLY = "monthly", "Monthly"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    donor = models.ForeignKey(
        Donor, on_delete=models.PROTECT, related_name="donations", null=True, blank=True,
        help_text="Leave empty for an anonymous gift (e.g. cash in a collection box).",
    )
    monthly_plan = models.ForeignKey(
        MonthlyPlan, on_delete=models.SET_NULL, related_name="donations", null=True, blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=POSITIVE_AMOUNT)
    received_on = models.DateField(default=timezone.localdate)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.BANK)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.MONTHLY)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    reference = models.CharField(max_length=100, blank=True, help_text="Bank reference or receipt number.")
    stripe_payment_id = models.CharField(max_length=100, blank=True, editable=False)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_on", "-created_at"]
        indexes = [models.Index(fields=["status", "received_on"])]

    def __str__(self):
        who = self.donor or "Anonymous"
        return f"£{self.amount} from {who} on {self.received_on:%d %b %Y}"

    def save(self, *args, **kwargs):
        # A payment linked to a monthly plan is always a monthly donation from that plan's donor.
        if self.monthly_plan_id:
            self.kind = self.Kind.MONTHLY
            if not self.donor_id:
                self.donor_id = self.monthly_plan.donor_id
        super().save(*args, **kwargs)
