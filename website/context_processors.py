from django.conf import settings

from .models import SiteSettings


def site(request):
    """Makes the group name and website settings available in every page template."""
    return {"site_name": settings.SITE_NAME, "site_settings": SiteSettings.load()}
