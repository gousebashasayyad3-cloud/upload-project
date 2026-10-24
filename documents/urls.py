from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),

    path(
        "upload/",
        views.upload_document,
        name="upload_document",
    ),

    path(
        "document/<uuid:document_id>/view/",
        views.view_document,
        name="view_document",
    ),

    path(
        "document/<uuid:document_id>/download/",
        views.download_document,
        name="download_document",
    ),

    path(
        "document/<uuid:document_id>/share/",
        views.share_document,
        name="share_document",
    ),

    path(
        "document/<uuid:document_id>/revoke/<int:user_id>/",
        views.revoke_access,
        name="revoke_access",
    ),
]