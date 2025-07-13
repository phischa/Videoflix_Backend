from django.urls import path, include
from auth_app.api import urls as auth_app_urls
from rest_framework.routers import DefaultRouter

urlpatterns = [
    path("", include(auth_app_urls)),
]