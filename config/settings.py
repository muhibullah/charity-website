"""
Django settings for the giving circle project.

Values that differ between your laptop and the live server (secret key,
debug mode, database) are read from environment variables / a .env file.
See .env.example.
"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


DEBUG = env_bool("DEBUG", False)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-insecure-key-change-me" if DEBUG else "")
if not SECRET_KEY:
    raise ImproperlyConfigured("Set SECRET_KEY in the .env file before running with DEBUG off.")
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

# The group's public name. Change it in .env (SITE_NAME=...) - no code change needed.
SITE_NAME = os.getenv("SITE_NAME", "Giving Circle")

INSTALLED_APPS = [
    # Unfold must come before django.contrib.admin
    "unfold",
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Our apps
    "donations",
    "aid",
    "stories",
    "website",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "website.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# SQLite on your laptop; set DATABASE_URL=postgres://... on the live server.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Live-server security (only when DEBUG is off) ---------------------------
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_CONTENT_TYPE_NOSNIFF = True

# --- Admin panel look & menu (django-unfold) ---------------------------------

UNFOLD = {
    "SITE_TITLE": f"{SITE_NAME} admin",
    "SITE_HEADER": SITE_NAME,
    "SITE_SUBHEADER": _("Admin panel"),
    "SITE_SYMBOL": "volunteer_activism",
    "DASHBOARD_CALLBACK": "config.dashboard.dashboard_callback",
    "COLORS": {
        # Green primary colour (instead of Unfold's default purple)
        "primary": {
            "50": "oklch(98.2% .018 155.826)",
            "100": "oklch(96.2% .044 156.743)",
            "200": "oklch(92.5% .084 155.995)",
            "300": "oklch(87.1% .15 154.449)",
            "400": "oklch(79.2% .209 151.711)",
            "500": "oklch(72.3% .219 149.579)",
            "600": "oklch(62.7% .194 149.214)",
            "700": "oklch(52.7% .154 150.069)",
            "800": "oklch(44.8% .119 151.328)",
            "900": "oklch(39.3% .095 152.535)",
            "950": "oklch(26.6% .065 152.934)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Overview"),
                "items": [
                    {"title": _("Dashboard"), "icon": "dashboard", "link": reverse_lazy("admin:index")},
                ],
            },
            {
                "title": _("Money in"),
                "separator": True,
                "items": [
                    {"title": _("Donors"), "icon": "group", "link": reverse_lazy("admin:donations_donor_changelist")},
                    {"title": _("Monthly plans"), "icon": "event_repeat", "link": reverse_lazy("admin:donations_monthlyplan_changelist")},
                    {"title": _("Donations"), "icon": "payments", "link": reverse_lazy("admin:donations_donation_changelist")},
                ],
            },
            {
                "title": _("Money out"),
                "separator": True,
                "items": [
                    {"title": _("Recipients"), "icon": "family_restroom", "link": reverse_lazy("admin:aid_recipient_changelist")},
                    {"title": _("Payouts"), "icon": "volunteer_activism", "link": reverse_lazy("admin:aid_payout_changelist")},
                ],
            },
            {
                "title": _("Website"),
                "separator": True,
                "items": [
                    {"title": _("Stories"), "icon": "article", "link": reverse_lazy("admin:stories_story_changelist")},
                    {"title": _("FAQs"), "icon": "help", "link": reverse_lazy("admin:website_faq_changelist")},
                    {"title": _("Website settings"), "icon": "settings", "link": reverse_lazy("admin:website_sitesettings_changelist")},
                ],
            },
            {
                "title": _("Admin users"),
                "separator": True,
                "items": [
                    {"title": _("Users"), "icon": "person", "link": reverse_lazy("admin:auth_user_changelist")},
                    {"title": _("Groups"), "icon": "shield_person", "link": reverse_lazy("admin:auth_group_changelist")},
                ],
            },
        ],
    },
}
