from pathlib import Path

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import SuspiciousFileOperation
from django.http import FileResponse, Http404
from django.utils._os import safe_join


@staff_member_required
def payout_proof(request, path):
    """Serve a payout receipt to logged-in admins only (receipts can show recipients' details)."""
    try:
        # Base is the receipts folder itself, so "../" can't reach other uploads.
        full_path = safe_join(Path(settings.MEDIA_ROOT, "payout-proofs"), path)
        return FileResponse(open(full_path, "rb"))
    except (SuspiciousFileOperation, FileNotFoundError, IsADirectoryError):
        raise Http404("File not found")
