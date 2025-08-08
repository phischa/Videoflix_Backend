import os
import re
from django.http import Http404, HttpResponse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from auth_app.authentication import CookieJWTAuthentication 
from video_app.models import Video
from .serializers import VideoListSerializer


from rest_framework.decorators import api_view, permission_classes

@api_view(['GET'])
@permission_classes([AllowAny])  # Kein Login für Test
def cors_test(request):
    """CORS Test Endpoint - prüft ob CORS funktioniert"""
    return Response({
        'message': 'CORS is working!',
        'origin': request.META.get('HTTP_ORIGIN', 'Unknown'),
        'method': request.method,
        'backend': 'Django Videoflix',
        'debug': settings.DEBUG
    })


@method_decorator(never_cache, name='dispatch')
class VideoListView(generics.ListAPIView):
    """
    API view for listing all available videos.
    
    Returns list of videos with basic information for authenticated users.
    Uses cookie-based JWT authentication and disables caching.
    """
    queryset = Video.objects.all()
    serializer_class = VideoListSerializer
    authentication_classes = [CookieJWTAuthentication]  
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        """Add request to serializer context for absolute URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def dispatch(self, request, *args, **kwargs):
        """Request dispatcher with debug logging."""
        print(f"DEBUG: Request to VideoListView")
        print(f"DEBUG: Authentication classes: {self.authentication_classes}")
        print(f"DEBUG: Cookies in request: {list(request.COOKIES.keys())}")
        return super().dispatch(request, *args, **kwargs)
    

class HLSManifestView(APIView):
    """
    API view for serving HLS manifest files (.m3u8).
    
    Provides HLS playlist files for video streaming in different resolutions.
    Validates video existence, resolution, and file availability.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, movie_id, resolution):
        """
        Serves HLS manifest file for specific video and resolution.
        
        Args:
            movie_id: ID of the requested video
            resolution: Video resolution (360p, 480p, 720p, 1080p)
            
        Returns:
            HttpResponse: Manifest file with proper content type
        """
        try:
            video = Video.objects.get(id=movie_id)
        except Video.DoesNotExist:
            return Response({"detail": "Video not found"}, status=404)
    
        # Resolution validation
        ALLOWED_RESOLUTIONS = ['360p', '480p', '720p', '1080p']
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
    """
    API view for serving HLS video segments (.ts files).
    
    Provides individual video segments for HLS streaming.
    Validates video, resolution, and segment name format.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, movie_id, resolution, segment):
        """
        Serves HLS video segment for specific video.
        
        Args:
            movie_id: ID of the requested video
            resolution: Video resolution 
            segment: Segment filename (e.g., 000.ts, index1.ts)
            
        Returns:
            HttpResponse: Video segment with proper content type
        """
        try:
            video = Video.objects.get(id=movie_id)
        except Video.DoesNotExist:
            return Response({"detail": "Video not found"}, status=404)

        ALLOWED_RESOLUTIONS = ['360p', '480p', '720p', '1080p']
        if resolution not in ALLOWED_RESOLUTIONS:
            return Response({"detail": "Invalid resolution"}, status=404)

        if not re.match(r'^(index\d+|\d{3})\.ts$', segment):
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
        