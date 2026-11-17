from django.db import models


class SiteSettings(models.Model):
    """Editable website text and contact details. There is only ever one row."""

    announcement = models.CharField(
        max_length=200, blank=True, help_text="Optional message shown in a strip at the top of every page."
    )
    tagline = models.CharField(max_length=150, default="Small monthly gifts. Real help for real people.")
    hero_image = models.ImageField(
        upload_to="site/", blank=True,
        help_text="Large photo at the top of the home page (landscape, at least 1600px wide). "
                  "Only use photos you own and have permission to share.",
    )
    intro = models.TextField(
        default="We are a group of friends who each give £10 or £20 a month. "
                "Together, we pass every penny directly to people and families who are struggling.",
        help_text="Shown under the headline on the home page.",
    )
    about_text = models.TextField(
        default="We started as a WhatsApp group of friends who wanted to do something simple: "
                "put a little aside each month and give it to people who need it most. "
                "No offices, no salaries - just neighbours helping neighbours.",
    )
    contact_email = models.EmailField(blank=True)
    whatsapp_link = models.URLField(blank=True, help_text="e.g. a WhatsApp group invite link or https://wa.me/447...")
    bank_account_name = models.CharField(max_length=100, blank=True)
    bank_sort_code = models.CharField(max_length=20, blank=True)
    bank_account_number = models.CharField(max_length=20, blank=True)
    bank_reference_hint = models.CharField(
        max_length=100, default="Your full name", help_text="What donors should write as the payment reference."
    )

    class Meta:
        verbose_name = verbose_name_plural = "website settings"

    def __str__(self):
        return "Website settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def has_bank_details(self):
        return bool(self.bank_account_number and self.bank_sort_code)


class FAQ(models.Model):
    question = models.CharField(max_length=200)
    answer = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question
