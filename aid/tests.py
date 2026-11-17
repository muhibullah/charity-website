import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase, override_settings


class PayoutProofTests(TestCase):
    """Payout receipts can show recipients' details, so only admins may open them."""

    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        folder = Path(self.media.name, "payout-proofs", "2026", "11")
        folder.mkdir(parents=True)
        (folder / "receipt.txt").write_text("receipt")
        Path(self.media.name, "secret.txt").write_text("outside")
        self.url = "/media/payout-proofs/2026/11/receipt.txt"

    def tearDown(self):
        self.media.cleanup()

    def test_visitors_are_sent_to_login(self):
        with override_settings(MEDIA_ROOT=self.media.name):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_admins_can_open_receipts(self):
        self.client.force_login(User.objects.create_superuser("boss", "b@example.com", "pw"))
        with override_settings(MEDIA_ROOT=self.media.name):
            response = self.client.get(self.url)
            self.assertEqual(b"".join(response.streaming_content), b"receipt")
            missing = self.client.get("/media/payout-proofs/nope.txt")
            escape = self.client.get("/media/payout-proofs/../secret.txt")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(escape.status_code, 404)
