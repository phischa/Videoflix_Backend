from django.urls import path, include
from auth_app.api import urls as auth_app_urls
from rest_framework.routers import DefaultRouter
from .views import VideoListView

urlpatterns = [
    path("", include(auth_app_urls)),
    path('video/', VideoListView.as_view(), name='video-list'),
]