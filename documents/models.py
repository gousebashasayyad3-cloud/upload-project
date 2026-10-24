import uuid
import hashlib
import json

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Document(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    title = models.CharField(max_length=255)

    file = models.FileField(
        upload_to="documents/",
        max_length=500,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_documents",
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class DocumentPermission(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="permissions",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_permissions",
    )

    can_view = models.BooleanField(default=True)

    can_download = models.BooleanField(default=False)

    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="permissions_granted",
    )

    granted_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "user"],
                name="unique_document_user_permission",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.document}"


class AuditEvent(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    action = models.CharField(max_length=100)

    result = models.CharField(max_length=20)

    timestamp = models.DateTimeField(
        default=timezone.now,
        editable=False,
    )

    details = models.JSONField(default=dict, blank=True)

    previous_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )

    event_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )

    def calculate_hash(self):
        payload = {
            "id": str(self.id),
            "actor_id": self.actor_id,
            "document_id": str(self.document_id)
            if self.document_id else None,
            "action": self.action,
            "result": self.result,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "previous_hash": self.previous_hash,
        }

        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(encoded).hexdigest()

    def __str__(self):
        return f"{self.action} - {self.result}"