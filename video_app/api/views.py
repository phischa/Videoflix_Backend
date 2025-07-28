from django.http import Http404
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
        # TODO: Hier kommt die Logik
        pass
