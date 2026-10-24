from django.contrib import admin
from django.urls import include, path
from documents import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("documents.urls")),
]