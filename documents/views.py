from pathlib import Path

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .audit import record_audit
from .forms import DocumentUploadForm
from .models import Document, DocumentPermission
from django.contrib.auth import get_user_model


User = get_user_model()


def user_can_view(user, document):
    if not user.is_authenticated:
        return False

    if not document.is_active:
        return False

    if document.owner_id == user.pk:
        return True

    if user.is_staff:
        return True

    return DocumentPermission.objects.filter(
        document=document,
        user=user,
        can_view=True,
    ).exists()


def user_can_download(user, document):
    if not user_can_view(user, document):
        return False

    if document.owner_id == user.pk or user.is_staff:
        return True

    return DocumentPermission.objects.filter(
        document=document,
        user=user,
        can_view=True,
        can_download=True,
    ).exists()


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = AuthenticationForm(
        request=request,
        data=request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect("dashboard")

    return render(
        request,
        "login.html",
        {"form": form},
    )


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    documents = Document.objects.filter(
        is_active=True,
    ).filter(
        owner=request.user,
    )

    shared_permissions = DocumentPermission.objects.filter(
        user=request.user,
        can_view=True,
        document__is_active=True,
    ).select_related("document", "document__owner")

    return render(
        request,
        "dashboard.html",
        {
            "documents": documents,
            "shared_permissions": shared_permissions,
        },
    )


@login_required
def upload_document(request):
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)

        if form.is_valid():
            document = form.save(commit=False)
            document.owner = request.user
            document.save()

            record_audit(
                actor=request.user,
                action="DOCUMENT_UPLOAD",
                result="SUCCESS",
                document=document,
            )

            messages.success(
                request,
                "Document uploaded successfully.",
            )

            return redirect("dashboard")

    else:
        form = DocumentUploadForm()

    return render(
        request,
        "upload.html",
        {"form": form},
    )


@login_required
def view_document(request, document_id):
    document = get_object_or_404(
        Document,
        id=document_id,
        is_active=True,
    )

    if not user_can_view(request.user, document):
        record_audit(
            actor=request.user,
            action="DOCUMENT_VIEW",
            result="DENIED",
            document=document,
        )

        raise Http404("Document not found.")

    record_audit(
        actor=request.user,
        action="DOCUMENT_VIEW",
        result="SUCCESS",
        document=document,
    )

    response = FileResponse(
        document.file.open("rb"),
        as_attachment=False,
        filename=Path(document.file.name).name,
    )

    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    response["Content-Security-Policy"] = "default-src 'none'; sandbox"

    return response


@login_required
def download_document(request, document_id):
    document = get_object_or_404(
        Document,
        id=document_id,
        is_active=True,
    )

    if not user_can_download(request.user, document):
        record_audit(
            actor=request.user,
            action="DOCUMENT_DOWNLOAD",
            result="DENIED",
            document=document,
        )

        raise Http404("Document not found.")

    record_audit(
        actor=request.user,
        action="DOCUMENT_DOWNLOAD",
        result="SUCCESS",
        document=document,
    )

    response = FileResponse(
        document.file.open("rb"),
        as_attachment=True,
        filename=Path(document.file.name).name,
    )

    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"

    return response


@login_required
@require_POST
def share_document(request, document_id):
    document = get_object_or_404(
        Document,
        id=document_id,
        is_active=True,
    )

    if document.owner_id != request.user.pk and not request.user.is_staff:
        record_audit(
            actor=request.user,
            action="DOCUMENT_SHARE",
            result="DENIED",
            document=document,
        )

        raise Http404("Document not found.")

    username = request.POST.get("username", "").strip()

    can_view = request.POST.get("can_view") == "on"
    can_download = request.POST.get("can_download") == "on"

    if not can_view and can_download:
        messages.error(
            request,
            "Download permission requires view permission.",
        )
        return redirect("dashboard")

    target_user = get_object_or_404(
        User,
        username=username,
        is_active=True,
    )

    if target_user.pk == document.owner_id:
        messages.error(
            request,
            "The owner already has access.",
        )
        return redirect("dashboard")

    permission, created = DocumentPermission.objects.update_or_create(
        document=document,
        user=target_user,
        defaults={
            "can_view": can_view,
            "can_download": can_download,
            "granted_by": request.user,
        },
    )

    record_audit(
        actor=request.user,
        action="DOCUMENT_SHARE",
        result="SUCCESS",
        document=document,
        details={
            "target_user_id": target_user.pk,
            "can_view": can_view,
            "can_download": can_download,
            "created": created,
        },
    )

    messages.success(
        request,
        "Document permissions updated.",
    )

    return redirect("dashboard")


@login_required
@require_POST
def revoke_access(request, document_id, user_id):
    document = get_object_or_404(
        Document,
        id=document_id,
        is_active=True,
    )

    if document.owner_id != request.user.pk and not request.user.is_staff:
        raise Http404("Document not found.")

    permission = get_object_or_404(
        DocumentPermission,
        document=document,
        user_id=user_id,
    )

    permission.delete()

    record_audit(
        actor=request.user,
        action="DOCUMENT_ACCESS_REVOKED",
        result="SUCCESS",
        document=document,
        details={"target_user_id": user_id},
    )

    messages.success(
        request,
        "Document access revoked.",
    )

    return redirect("dashboard")