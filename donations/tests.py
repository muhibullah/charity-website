from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from aid.models import Payout, Recipient
from donations import reports
from donations.models import Donation, Donor, MonthlyPlan
from stories.models import Story


class ReportTests(TestCase):
    def setUp(self):
        self.donor = Donor.objects.create(first_name="Amina")
        self.plan = MonthlyPlan.objects.create(donor=self.donor, amount=Decimal("10"))
        MonthlyPlan.objects.create(donor=self.donor, amount=Decimal("5"), status=MonthlyPlan.Status.CANCELLED)
        Donation.objects.create(donor=self.donor, amount=Decimal("10"), received_on=date(2026, 10, 3))
        Donation.objects.create(donor=self.donor, amount=Decimal("20"), received_on=date(2026, 11, 3))
        Donation.objects.create(donor=self.donor, amount=Decimal("99"), received_on=date(2026, 11, 4),
                                status=Donation.Status.FAILED)
        self.recipient = Recipient.objects.create(display_name="A family")
        Payout.objects.create(recipient=self.recipient, amount=Decimal("25"), paid_on=date(2026, 11, 10))

    def test_overall_totals_ignore_failed_donations_and_cancelled_plans(self):
        totals = reports.overall_totals()
        self.assertEqual(totals["money_in"], Decimal("30"))
        self.assertEqual(totals["money_out"], Decimal("25"))
        self.assertEqual(totals["balance"], Decimal("5"))
        self.assertEqual(totals["people_helped"], 1)
        self.assertEqual(totals["active_donors"], 1)
        self.assertEqual(totals["monthly_committed"], Decimal("10"))

    def test_monthly_summary_newest_first_with_empty_months(self):
        rows = reports.monthly_summary(3, today=date(2026, 11, 15))
        self.assertEqual([r["month"] for r in rows], [date(2026, 11, 1), date(2026, 10, 1), date(2026, 9, 1)])
        self.assertEqual(rows[0]["money_in"], Decimal("20"))
        self.assertEqual(rows[0]["money_out"], Decimal("25"))
        self.assertEqual(rows[2]["money_in"], Decimal("0"))

    def test_add_months_crosses_years(self):
        self.assertEqual(reports.add_months(date(2026, 1, 1), -1), date(2025, 12, 1))
        self.assertEqual(reports.add_months(date(2026, 12, 1), 1), date(2027, 1, 1))


class ModelTests(TestCase):
    def test_plan_donation_takes_donor_and_monthly_kind(self):
        donor = Donor.objects.create(first_name="Omar")
        plan = MonthlyPlan.objects.create(donor=donor, amount=Decimal("20"))
        donation = Donation.objects.create(monthly_plan=plan, amount=Decimal("20"), kind=Donation.Kind.ONE_OFF)
        self.assertEqual(donation.donor, donor)
        self.assertEqual(donation.kind, Donation.Kind.MONTHLY)

    def test_recipient_gets_reference(self):
        recipient = Recipient.objects.create(display_name="A family")
        self.assertEqual(recipient.reference, f"R-{recipient.pk:04d}")

    def test_story_needs_recipient_consent(self):
        recipient = Recipient.objects.create(display_name="A family", consent_to_publish=False)
        story = Story(title="T", slug="t", summary="s", body="b", recipient=recipient)
        with self.assertRaises(ValidationError):
            story.full_clean()

    def test_donor_public_name(self):
        self.assertEqual(Donor(first_name="Sara", show_name_publicly=False).public_name, "Anonymous")
        self.assertEqual(Donor(first_name="Sara", last_name="Khan", show_name_publicly=True).public_name, "Sara Khan")


class AdminPagesTests(TestCase):
    """Every admin page opens without errors (with demo data loaded)."""

    @classmethod
    def setUpTestData(cls):
        with override_settings(DEBUG=True):
            call_command("seed_demo", stdout=StringIO())
        cls.admin = User.objects.create_superuser("admin", "admin@example.com", "test-pass-123")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_dashboard(self):
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "Balance available")
        self.assertContains(response, "Last 6 months")

    def test_list_and_add_pages(self):
        for name in ["donations_donor", "donations_monthlyplan", "donations_donation",
                     "aid_recipient", "aid_payout", "stories_story", "website_faq", "auth_user"]:
            for page in ["changelist", "add"]:
                with self.subTest(name=name, page=page):
                    self.assertEqual(self.client.get(reverse(f"admin:{name}_{page}")).status_code, 200)

    def test_donor_totals_not_double_counted(self):
        donor = Donor.objects.filter(donations__isnull=False).first()
        expected = sum(d.amount for d in donor.donations.filter(status=Donation.Status.COMPLETED))
        response = self.client.get(reverse("admin:donations_donor_changelist"), {"q": donor.phone})
        self.assertContains(response, f"£{expected:,.2f}")

    def test_csv_export(self):
        ids = list(Donation.objects.values_list("pk", flat=True)[:3])
        response = self.client.post(reverse("admin:donations_donation_changelist"),
                                    {"action": "export_as_csv", "_selected_action": ids})
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertEqual(len(response.content.decode().strip().splitlines()), 4)  # header + 3 rows
