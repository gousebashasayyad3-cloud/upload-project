from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Document


User = get_user_model()


class DocumentSecurityTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            password="TestPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="other",
            password="TestPassword123!",
        )

        self.document = Document.objects.create(
            title="Confidential Test",
            owner=self.owner,
            file=SimpleUploadedFile(
                "test.txt",
                b"Confidential test content",
                content_type="text/plain",
            ),
        )

    def test_unauthenticated_user_cannot_view_document(self):
        response = self.client.get(
            reverse(
                "view_document",
                args=[self.document.id],
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_unauthorized_user_cannot_download_document(self):
        self.client.login(
            username="other",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "download_document",
                args=[self.document.id],
            )
        )

        self.assertEqual(response.status_code, 404)