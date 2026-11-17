from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from aid.views import payout_proof

urlpatterns = [
    path("admin/", admin.site.urls),
    # Payout receipts are private: only logged-in admins can open them, in every environment.
    path(f"{settings.MEDIA_URL.lstrip('/')}payout-proofs/<path:path>", payout_proof, name="payout_proof"),
    path("", include("website.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
