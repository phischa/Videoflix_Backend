import os
import re
from django.http import Http404, HttpResponse 
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from auth_app.authentication import CookieJWTAuthentication 
from video_app.models import Video
from .serializers import VideoListSerializer


class VideoListView(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoListSerializer
    authentication_classes = [CookieJWTAuthentication]  
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        print(f"DEBUG: Request to VideoListView")
        print(f"DEBUG: Authentication classes: {self.authentication_classes}")
        print(f"DEBUG: Cookies in request: {list(request.COOKIES.keys())}")
        return super().dispatch(request, *args, **kwargs)
    

class HLSManifestView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, movie_id, resolution):
        try:
            video = Video.objects.get(id=movie_id)
        except Video.DoesNotExist:
            return Response({"detail": "Video not found"}, status=404)
    
        # Resolution validation
        ALLOWED_RESOLUTIONS = ['120p', '360p', '720p', '1080p']
        if resolution not in ALLOWED_RESOLUTIONS:
            return Response({"detail": "Invalid resolution"}, status=404)
        
        # File-Path konstruieren
        hls_file_path = f"media/hls/{video.id}/{resolution}/index.m3u8"

        # Prüfen ob File existiert
        if not os.path.exists(hls_file_path):
            return Response({"detail": "Manifest not found"}, status=404)
        
        # File lesen
        with open(hls_file_path, 'r') as f:
            manifest_content = f.read()

        # Raw-Content mit korrektem Content-Type zurückgeben
        return HttpResponse(
            manifest_content, 
            content_type='application/vnd.apple.mpegurl'
        )         
    

class HLSSegmentView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, movie_id, resolution, segment):
        try:
            video = Video.objects.get(id=movie_id)
        except Video.DoesNotExist:
            return Response({"detail": "Video not found"}, status=404)

        ALLOWED_RESOLUTIONS = ['120p', '360p', '720p', '1080p']
        if resolution not in ALLOWED_RESOLUTIONS:
            return Response({"detail": "Invalid resolution"}, status=404)

        if not re.match(r'^\d{3}\.ts$', segment):  # nur 000.ts, 001.ts, etc.
            return Response({"detail": "Invalid segment name"}, status=404)

        # File-Path konstruieren
        segment_file_path = f"media/hls/{video.id}/{resolution}/{segment}"

        # Prüfen ob File existiert
        if not os.path.exists(segment_file_path):
            return Response({"detail": "Segment not found"}, status=404)

        # File lesen (BINÄR für .ts files!)
        with open(segment_file_path, 'rb') as f:  # 'rb' = read binary
            segment_content = f.read()

        # Raw-Content mit Video-Content-Type zurückgeben
        return HttpResponse(
            segment_content,
            content_type='video/MP2T'
        )