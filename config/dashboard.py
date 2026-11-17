from aid.models import Payout
from donations import reports
from donations.models import Donation, Donor


def money(value):
    sign = "-" if value < 0 else ""
    return f"{sign}£{abs(value):,.2f}"


def dashboard_callback(request, context):
    """Extra data for the admin home page (templates/admin/index.html)."""
    overall = reports.overall_totals()
    this_month = reports.this_month_totals()

    context.update({
        "stats": [
            {"label": "Balance available", "value": money(overall["balance"]),
             "note": f"{money(overall['money_in'])} in, {money(overall['money_out'])} out"},
            {"label": f"Donations in {this_month['month']:%B}", "value": money(this_month["money_in"]),
             "note": f"Given out: {money(this_month['money_out'])}"},
            {"label": "Monthly donors", "value": overall["active_donors"],
             "note": f"{money(overall['monthly_committed'])} promised per month"},
            {"label": "People helped", "value": overall["people_helped"],
             "note": f"{overall['total_donors']} donors in total"},
        ],
        "monthly_table": {
            "headers": ["Month", "Money in", "Money out", "Difference"],
            "rows": [
                [f"{row['month']:%B %Y}", money(row["money_in"]), money(row["money_out"]),
                 money(row["money_in"] - row["money_out"])]
                for row in reports.monthly_summary(6)
            ],
        },
        "recent_donations": {
            "headers": ["Date", "Donor", "Amount", "Method"],
            "rows": [
                [f"{d.received_on:%d %b}", str(d.donor or "Anonymous"), money(d.amount), d.get_method_display()]
                for d in Donation.objects.filter(status=Donation.Status.COMPLETED).select_related("donor")[:6]
            ],
        },
        "new_signups": {
            "headers": ["Joined", "Name", "Email", "Phone"],
            "rows": [
                [f"{d.joined_on:%d %b}", str(d), d.email, d.phone or "-"]
                for d in Donor.objects.filter(source=Donor.Source.WEBSITE, monthly_plans__isnull=True)
                .order_by("-created_at")[:6]
            ],
        },
        "recent_payouts": {
            "headers": ["Date", "Recipient", "Amount", "Purpose"],
            "rows": [
                [f"{p.paid_on:%d %b}", p.recipient.display_name, money(p.amount), p.get_purpose_display()]
                for p in Payout.objects.select_related("recipient")[:6]
            ],
        },
    })
    return context
