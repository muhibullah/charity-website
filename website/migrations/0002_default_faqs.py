from django.db import migrations

# Starter questions - edit or replace them in the admin panel (Website > FAQs).
DEFAULT_FAQS = [
    ("Where does my money go?",
     "Every penny goes directly to people in need - as cash, bank transfers or essentials like food and bills. "
     "We have no offices or salaries. You can see every month's money in and money out on our "
     "'Where the money goes' page."),
    ("How much do I have to give?",
     "Most members give £10 or £20 a month, but any amount helps. You can also make a one-off gift."),
    ("Can I stop or change my donation?",
     "Yes, any time. Just contact us and we'll change or stop it - no questions asked."),
    ("How do you choose who to help?",
     "Members suggest people and families they know are struggling. We check each case and agree "
     "together where the month's money should go."),
    ("Are you a registered charity?",
     "Not yet. We are a community giving group. If our yearly income grows past the Charity Commission's "
     "threshold (£5,000), we will register."),
    ("Will my name be shown on the website?",
     "Only if you say so. Otherwise you are listed as 'Anonymous'. We never share your details with anyone."),
]


def add_faqs(apps, schema_editor):
    FAQ = apps.get_model("website", "FAQ")
    for order, (question, answer) in enumerate(DEFAULT_FAQS):
        FAQ.objects.get_or_create(question=question, defaults={"answer": answer, "order": order})


def remove_faqs(apps, schema_editor):
    FAQ = apps.get_model("website", "FAQ")
    FAQ.objects.filter(question__in=[q for q, _ in DEFAULT_FAQS]).delete()


class Migration(migrations.Migration):
    dependencies = [("website", "0001_initial")]
    operations = [migrations.RunPython(add_faqs, remove_faqs)]
