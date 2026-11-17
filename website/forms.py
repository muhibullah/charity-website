from decimal import Decimal

from django import forms
from django.utils import timezone

from donations.models import Donor


class JoinForm(forms.Form):
    """Sign-up form on the Donate page. Creates a donor record for the admins to follow up."""

    AMOUNT_CHOICES = [("10", "£10"), ("20", "£20"), ("50", "£50"), ("other", "Other")]
    FREQUENCY_CHOICES = [("monthly", "Every month"), ("one_off", "Just once")]

    frequency = forms.ChoiceField(choices=FREQUENCY_CHOICES, widget=forms.RadioSelect, initial="monthly")
    amount = forms.ChoiceField(choices=AMOUNT_CHOICES, widget=forms.RadioSelect, initial="10")
    other_amount = forms.DecimalField(
        required=False, min_value=Decimal("1"), max_value=Decimal("10000"), decimal_places=2,
        label="Other amount (£)",
    )
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100, required=False)
    email = forms.EmailField()
    phone = forms.CharField(max_length=30, required=False, label="Phone / WhatsApp (optional)")
    show_name_publicly = forms.BooleanField(
        required=False, label="You may thank me by name on the website (otherwise I'll be listed as Anonymous)"
    )
    consent = forms.BooleanField(
        label="I agree that the group stores my details to manage my donations and contact me about them."
    )
    # Hidden "honeypot" field: real people never fill it in, spam bots usually do.
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    def clean(self):
        data = super().clean()
        if data.get("amount") == "other" and not data.get("other_amount"):
            self.add_error("other_amount", "Please enter an amount.")
        return data

    @property
    def is_spam(self):
        return bool(self.cleaned_data.get("website"))

    def chosen_amount(self):
        data = self.cleaned_data
        return data["other_amount"] if data["amount"] == "other" else Decimal(data["amount"])

    def save(self):
        data = self.cleaned_data
        frequency = dict(self.FREQUENCY_CHOICES)[data["frequency"]].lower()
        note = f"Signed up on the website on {timezone.localdate():%d %b %Y}: wants to give £{self.chosen_amount():.2f} {frequency}."

        donor = Donor.objects.filter(email__iexact=data["email"]).first()
        if donor:
            donor.notes = f"{donor.notes}\n{note}".strip()
            donor.save(update_fields=["notes"])
            return donor
        return Donor.objects.create(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone=data["phone"],
            show_name_publicly=data["show_name_publicly"],
            source=Donor.Source.WEBSITE,
            notes=note,
        )
