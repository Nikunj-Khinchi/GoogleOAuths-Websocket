from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("google/login/", views.google_login, name="google_login"),
    path("google/callback/", views.google_callback, name="google_callback"),
    path("google/logout/", views.google_logout, name="google_logout"),
    path("google/drive/upload/", views.upload_to_drive, name="upload_to_drive"),
    path("google/drive/files/", views.fetch_drive_files, name="fetch_drive_files"),
]
