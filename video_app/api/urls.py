from django.urls import path, include
from auth_app.api import urls as auth_app_urls
from rest_framework.routers import DefaultRouter
from .views import VideoListView, HLSManifestView, HLSSegmentView, cors_test

urlpatterns = [
    path('video/', VideoListView.as_view(), name='video-list'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', 
        HLSManifestView.as_view(), 
        name='hls-manifest'),
    path('video/<int:movie_id>/<str:resolution>/<str:segment>', 
        HLSSegmentView.as_view(), 
        name='hls-segment'),
    path('cors-test/', cors_test, name='cors-test'),
]
