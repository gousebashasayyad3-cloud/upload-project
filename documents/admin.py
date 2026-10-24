from django.contrib import admin

from .models import Document, DocumentPermission, AuditEvent


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "created_at",
        "is_active",
    )

    search_fields = (
        "title",
        "owner__username",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    readonly_fields = (
        "id",
        "created_at",
    )


@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "document",
        "user",
        "can_view",
        "can_download",
        "granted_by",
        "granted_at",
    )

    list_filter = (
        "can_view",
        "can_download",
    )

    readonly_fields = (
        "granted_at",
    )


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "actor",
        "action",
        "result",
        "document",
    )

    list_filter = (
        "action",
        "result",
        "timestamp",
    )

    readonly_fields = (
        "id",
        "actor",
        "document",
        "action",
        "result",
        "timestamp",
        "details",
        "previous_hash",
        "event_hash",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False