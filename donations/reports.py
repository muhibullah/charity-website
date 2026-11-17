"""
Totals used by the admin dashboard (and later the public "Where the money goes" page).

Everything is calculated from the Donation and Payout tables, so the numbers
always match the records - nobody types a total by hand.
"""

from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from aid.models import Payout, Recipient
from donations.models import Donation, Donor, MonthlyPlan

ZERO = Decimal("0.00")


def completed_donations():
    return Donation.objects.filter(status=Donation.Status.COMPLETED)


def _sum(queryset, field="amount"):
    return queryset.aggregate(total=Sum(field))["total"] or ZERO


def month_start(d):
    return d.replace(day=1)


def add_months(d, months):
    """First day of the month `months` away from d (negative = earlier)."""
    index = d.year * 12 + (d.month - 1) + months
    return date(index // 12, index % 12 + 1, 1)


def overall_totals():
    money_in = _sum(completed_donations())
    money_out = _sum(Payout.objects.all())
    active_plans = MonthlyPlan.objects.filter(status=MonthlyPlan.Status.ACTIVE)
    return {
        "money_in": money_in,
        "money_out": money_out,
        "balance": money_in - money_out,
        "people_helped": Recipient.objects.filter(payouts__isnull=False).distinct().count(),
        "active_donors": active_plans.values("donor").distinct().count(),
        "monthly_committed": _sum(active_plans),
        "total_donors": Donor.objects.filter(is_active=True).count(),
    }


def this_month_totals(today=None):
    today = today or timezone.localdate()
    start, end = month_start(today), add_months(today, 1)
    money_in = _sum(completed_donations().filter(received_on__gte=start, received_on__lt=end))
    money_out = _sum(Payout.objects.filter(paid_on__gte=start, paid_on__lt=end))
    return {"month": start, "money_in": money_in, "money_out": money_out}


def payouts_by_purpose():
    """Total given out per purpose (food, rent, ...), biggest first, with a percentage for bar charts."""
    labels = dict(Payout.Purpose.choices)
    rows = Payout.objects.values("purpose").annotate(total=Sum("amount")).order_by("-total")
    grand_total = sum((r["total"] for r in rows), ZERO)
    return [
        {"purpose": labels.get(r["purpose"], r["purpose"]), "total": r["total"],
         "percent": round(r["total"] / grand_total * 100) if grand_total else 0}
        for r in rows
    ]


def monthly_summary(months=6, today=None):
    """Money in / out for each of the last `months` months, newest first."""
    today = today or timezone.localdate()
    first = add_months(month_start(today), -(months - 1))

    def by_month(queryset, date_field):
        rows = (
            queryset.filter(**{f"{date_field}__gte": first})
            .annotate(month=TruncMonth(date_field))
            .values("month")
            .annotate(total=Sum("amount"))
        )
        return {row["month"]: row["total"] for row in rows}

    money_in = by_month(completed_donations(), "received_on")
    money_out = by_month(Payout.objects.all(), "paid_on")

    summary = []
    for i in range(months):
        m = add_months(first, i)
        summary.append({"month": m, "money_in": money_in.get(m, ZERO), "money_out": money_out.get(m, ZERO)})
    return list(reversed(summary))
