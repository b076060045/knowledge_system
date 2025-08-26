from django.contrib import admin
from django.urls import path
from rag.view import upload_file

urlpatterns = [
    path("admin/", admin.site.urls),
    path("upload/", upload_file.upload_file)
]