from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from video_app.models import Video
from .serializers import VideoListSerializer


class VideoListView(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoListSerializer
    permission_classes = [IsAuthenticated]