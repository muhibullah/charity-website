from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from aid.models import Payout
from donations import reports
from stories.models import Story

from .forms import JoinForm
from .models import FAQ


def published_faqs():
    return FAQ.objects.filter(is_published=True)


def home(request):
    return render(request, "website/home.html", {
        "totals": reports.overall_totals(),
        "stories": Story.published.all()[:3],
        "faqs": published_faqs()[:4],
    })


def how_it_works(request):
    return render(request, "website/how_it_works.html", {"totals": reports.overall_totals()})


def impact(request):
    months = reports.monthly_summary(12)
    # Drop the empty months from before the group started (oldest rows are at the end).
    while len(months) > 1 and not (months[-1]["money_in"] or months[-1]["money_out"]):
        months.pop()
    return render(request, "website/impact.html", {
        "totals": reports.overall_totals(),
        "months": months,
        "purposes": reports.payouts_by_purpose(),
        # Only date, purpose and amount - never who received it.
        "recent_payouts": Payout.objects.order_by("-paid_on", "-created_at")[:10],
    })


def story_list(request):
    page = Paginator(Story.published.all(), 9).get_page(request.GET.get("page"))
    return render(request, "website/story_list.html", {"page": page})


def story_detail(request, slug):
    story = get_object_or_404(Story.published.select_related("recipient"), slug=slug)
    more = Story.published.exclude(pk=story.pk)[:3]
    return render(request, "website/story_detail.html", {"story": story, "more_stories": more})


def donate(request):
    # The home page donation box links here with ?frequency=monthly&amount=20 to pre-select the choices.
    initial = {}
    if request.GET.get("frequency") in dict(JoinForm.FREQUENCY_CHOICES):
        initial["frequency"] = request.GET["frequency"]
    if request.GET.get("amount") in dict(JoinForm.AMOUNT_CHOICES):
        initial["amount"] = request.GET["amount"]
    form = JoinForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        if not form.is_spam:
            form.save()
        request.session["joined"] = {
            "name": form.cleaned_data["first_name"],
            "amount": f"{form.chosen_amount():.2f}",
            "frequency": form.cleaned_data["frequency"],
        }
        return redirect("website:thanks")
    return render(request, "website/donate.html", {"form": form})


def thanks(request):
    joined = request.session.pop("joined", None)
    if not joined:
        return redirect("website:donate")
    return render(request, "website/thanks.html", {"joined": joined})


def about(request):
    return render(request, "website/about.html", {"totals": reports.overall_totals()})


def faq(request):
    return render(request, "website/faq.html", {"faqs": published_faqs()})


def contact(request):
    return render(request, "website/contact.html")


def privacy(request):
    return render(request, "website/privacy.html")
