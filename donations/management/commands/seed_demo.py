"""
Fill the database with made-up demo data so you can try the admin panel.

    python manage.py seed_demo          # add demo data
    python manage.py seed_demo --reset  # delete ALL donors/donations/payouts/stories first

Only for your laptop - never run this on the live site.
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from aid.models import Payout, Recipient
from donations.models import Donation, Donor, MonthlyPlan
from donations.reports import add_months, month_start
from stories.models import Story

FIRST_NAMES = ["Amina", "Yusuf", "Fatima", "Omar", "Sara", "Bilal", "Layla", "Hamza", "Noor", "Idris",
               "Maryam", "Zaid", "Hana", "Tariq", "Aisha", "Karim", "Leah", "Daniel", "Priya", "Sam",
               "Grace", "Ali"]
LAST_NAMES = ["Rahman", "Khan", "Hussain", "Ahmed", "Patel", "Smith", "Begum", "Malik", "Jones", "Ali"]


class Command(BaseCommand):
    help = "Create made-up demo data for trying out the admin panel."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing records first.")

    @transaction.atomic
    def handle(self, *args, reset=False, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo only runs with DEBUG=True (never on the live site).")

        if reset:
            for model in (Story, Payout, Recipient, Donation, MonthlyPlan, Donor):
                model.objects.all().delete()
        elif Donor.objects.exists():
            raise CommandError("There is already data. Use --reset to replace it with demo data.")

        rng = random.Random(42)
        today = timezone.localdate()
        first_month = add_months(month_start(today), -5)

        # 22 donors from the WhatsApp group, each giving £10 or £20 a month
        donors = []
        for i, first in enumerate(FIRST_NAMES):
            donor = Donor.objects.create(
                first_name=first,
                last_name=rng.choice(LAST_NAMES),
                phone=f"07700 900{i:03d}",
                email=f"{first.lower()}@example.com" if i % 3 else "",
                source=Donor.Source.WHATSAPP if i < 18 else Donor.Source.WEBSITE,
                show_name_publicly=i % 4 == 0,
                joined_on=first_month - timedelta(days=rng.randint(0, 200)),
            )
            plan = MonthlyPlan.objects.create(
                donor=donor,
                amount=Decimal(rng.choice([10, 10, 20])),
                method=MonthlyPlan.Method.STRIPE if donor.source == Donor.Source.WEBSITE else MonthlyPlan.Method.STANDING_ORDER,
                day_of_month=rng.randint(1, 28),
                started_on=donor.joined_on,
            )
            donors.append((donor, plan))

        # Six months of monthly payments (current month only up to today)
        for m in range(6):
            month = add_months(first_month, m)
            for donor, plan in donors:
                paid_on = month.replace(day=plan.day_of_month)
                if paid_on > today or rng.random() < 0.08:  # a few people miss a month
                    continue
                Donation.objects.create(
                    donor=donor, monthly_plan=plan, amount=plan.amount, received_on=paid_on,
                    method=Donation.Method.STRIPE if plan.method == MonthlyPlan.Method.STRIPE else Donation.Method.BANK,
                    reference=f"GC-{donor.pk:03d}-{month:%m%y}",
                )

        # A couple of one-off gifts
        Donation.objects.create(amount=Decimal("50"), method=Donation.Method.CASH, kind=Donation.Kind.ONE_OFF,
                                received_on=today - timedelta(days=20), notes="Cash collection after Friday prayers")
        Donation.objects.create(donor=donors[2][0], amount=Decimal("100"), kind=Donation.Kind.ONE_OFF,
                                received_on=today - timedelta(days=45))

        # Families helped
        families = [
            ("A mother of three in Bradford", "Bradford, UK", 4, True),
            ("An elderly couple", "Birmingham, UK", 2, True),
            ("A refugee family", "Manchester, UK", 5, False),
            ("A student", "London, UK", 1, False),
            ("A widow and her children", "Sylhet, Bangladesh", 4, True),
            ("A family recovering from flooding", "Sindh, Pakistan", 7, True),
        ]
        recipients = [
            Recipient.objects.create(display_name=name, location=loc, household_size=size, consent_to_publish=consent,
                                     situation="Demo record - not a real person.")
            for name, loc, size, consent in families
        ]

        purposes = [Payout.Purpose.FOOD, Payout.Purpose.RENT, Payout.Purpose.BILLS, Payout.Purpose.MEDICAL]
        for m in range(6):
            month = add_months(first_month, m)
            paid_on = month.replace(day=25)
            if paid_on > today:
                continue
            for recipient in rng.sample(recipients, 2):
                Payout.objects.create(recipient=recipient, amount=Decimal(rng.choice([100, 120, 150])),
                                      paid_on=paid_on, purpose=rng.choice(purposes))

        Story.objects.create(
            title="Food and heating for a family in Bradford",
            slug="food-and-heating-bradford",
            summary="Your monthly gifts paid for a month of food shopping and the gas bill.",
            body="This is a demo story. Replace it with a real update from your group.",
            recipient=recipients[0], is_published=True, published_on=today - timedelta(days=10),
        )
        Story.objects.create(
            title="Helping after the floods",
            slug="helping-after-the-floods",
            summary="A draft story - not published yet.",
            body="This is a demo draft.",
            recipient=recipients[5],
        )

        self.stdout.write(self.style.SUCCESS(
            f"Demo data created: {Donor.objects.count()} donors, {Donation.objects.count()} donations, "
            f"{Recipient.objects.count()} recipients, {Payout.objects.count()} payouts, {Story.objects.count()} stories."
        ))
