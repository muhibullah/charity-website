from django.urls import path

from . import views

app_name = "website"

urlpatterns = [
    path("", views.home, name="home"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("where-the-money-goes/", views.impact, name="impact"),
    path("stories/", views.story_list, name="story_list"),
    path("stories/<slug:slug>/", views.story_detail, name="story_detail"),
    path("donate/", views.donate, name="donate"),
    path("donate/thank-you/", views.thanks, name="thanks"),
    path("about/", views.about, name="about"),
    path("faq/", views.faq, name="faq"),
    path("contact/", views.contact, name="contact"),
    path("privacy/", views.privacy, name="privacy"),
]
