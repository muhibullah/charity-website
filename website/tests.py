from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from aid.models import Payout, Recipient
from donations.models import Donation, Donor
from stories.models import Story

from .models import FAQ, SiteSettings


def join_data(**overrides):
    data = {
        "frequency": "monthly", "amount": "20", "first_name": "Sara", "last_name": "Khan",
        "email": "sara@example.com", "phone": "", "consent": "on", "website": "",
    }
    data.update(overrides)
    return data


class PageTests(TestCase):
    def setUp(self):
        donor = Donor.objects.create(first_name="Amina")
        Donation.objects.create(donor=donor, amount=Decimal("1500"))
        self.recipient = Recipient.objects.create(display_name="A family in Leeds", full_name="Secret Surname",
                                                  consent_to_publish=True)
        Payout.objects.create(recipient=self.recipient, amount=Decimal("120"), purpose=Payout.Purpose.RENT)
        self.story = Story.objects.create(title="Rent paid", slug="rent-paid", summary="Summary", body="Body",
                                          recipient=self.recipient, is_published=True)
        Story.objects.create(title="Secret draft", slug="draft", summary="s", body="b")

    def test_all_pages_load(self):
        for name in ["home", "how_it_works", "impact", "story_list", "donate", "about", "faq", "contact", "privacy"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(f"website:{name}")).status_code, 200)

    def test_home_shows_live_totals_and_published_stories_only(self):
        response = self.client.get(reverse("website:home"))
        self.assertContains(response, "£120")
        self.assertContains(response, "£1,500")
        self.assertContains(response, "Rent paid")
        self.assertNotContains(response, "Secret draft")

    def test_draft_story_is_404(self):
        self.assertEqual(self.client.get(reverse("website:story_detail", args=["draft"])).status_code, 404)
        self.assertEqual(self.client.get(reverse("website:story_detail", args=["rent-paid"])).status_code, 200)

    def test_impact_never_shows_private_names(self):
        response = self.client.get(reverse("website:impact"))
        self.assertContains(response, "Rent / housing")
        self.assertNotContains(response, "Secret Surname")
        self.assertNotContains(response, "A family in Leeds")

    def test_faqs_from_database(self):
        FAQ.objects.create(question="Is this a test?", answer="Yes")
        FAQ.objects.create(question="Hidden question?", answer="No", is_published=False)
        response = self.client.get(reverse("website:faq"))
        self.assertContains(response, "Is this a test?")
        self.assertNotContains(response, "Hidden question?")

    def test_bank_details_only_when_filled_in(self):
        self.assertNotContains(self.client.get(reverse("website:donate")), "Sort code")
        settings = SiteSettings.load()
        settings.bank_sort_code, settings.bank_account_number = "12-34-56", "12345678"
        settings.save()
        self.assertContains(self.client.get(reverse("website:donate")), "12345678")


class JoinFormTests(TestCase):
    def test_signup_creates_website_donor(self):
        response = self.client.post(reverse("website:donate"), join_data(), follow=True)
        self.assertContains(response, "Thank you, Sara!")
        self.assertContains(response, "£20 every month")
        donor = Donor.objects.get(email="sara@example.com")
        self.assertEqual(donor.source, Donor.Source.WEBSITE)
        self.assertIn("£20.00 every month", donor.notes)

    def test_other_amount_required_when_chosen(self):
        response = self.client.post(reverse("website:donate"), join_data(amount="other"))
        self.assertContains(response, "Please enter an amount.")
        self.assertFalse(Donor.objects.exists())

    def test_other_amount_one_off(self):
        self.client.post(reverse("website:donate"), join_data(amount="other", other_amount="35", frequency="one_off"))
        self.assertIn("£35.00 just once", Donor.objects.get().notes)

    def test_consent_required(self):
        data = join_data()
        del data["consent"]
        self.client.post(reverse("website:donate"), data)
        self.assertFalse(Donor.objects.exists())

    def test_existing_email_adds_note_instead_of_duplicate(self):
        Donor.objects.create(first_name="Sara", email="SARA@example.com", notes="Old note")
        self.client.post(reverse("website:donate"), join_data())
        donor = Donor.objects.get()
        self.assertIn("Old note", donor.notes)
        self.assertIn("wants to give £20.00", donor.notes)

    def test_honeypot_blocks_bots(self):
        response = self.client.post(reverse("website:donate"), join_data(website="http://spam"))
        self.assertRedirects(response, reverse("website:thanks"))
        self.assertFalse(Donor.objects.exists())

    def test_thanks_page_without_signup_redirects(self):
        self.assertRedirects(self.client.get(reverse("website:thanks")), reverse("website:donate"))
