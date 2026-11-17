from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from aid.models import Recipient


class PublishedStoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True, published_on__lte=timezone.localdate())


class Story(models.Model):
    """A public update shown on the website: who was helped, what the money did."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, help_text="Part of the web address, e.g. 'food-for-winter'.")
    summary = models.CharField(max_length=300, help_text="One or two sentences shown on the story list.")
    body = models.TextField()
    image = models.ImageField(upload_to="stories/%Y/%m/", blank=True)
    recipient = models.ForeignKey(
        Recipient, on_delete=models.SET_NULL, null=True, blank=True, related_name="stories",
        help_text="Optional. Only recipients who gave consent can be linked.",
    )
    is_published = models.BooleanField(default=False)
    published_on = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published = PublishedStoryManager()

    class Meta:
        ordering = ["-published_on", "-created_at"]
        verbose_name_plural = "stories"

    def __str__(self):
        return self.title

    def clean(self):
        if self.recipient and not self.recipient.consent_to_publish:
            raise ValidationError({"recipient": "This recipient has not agreed to be featured on the website."})
