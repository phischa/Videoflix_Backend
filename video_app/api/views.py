from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from auth_app.authentication import CookieJWTAuthentication 
from video_app.models import Video
from .serializers import VideoListSerializer


class VideoListView(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoListSerializer
    authentication_classes = [CookieJWTAuthentication]  
    permission_classes = [IsAuthenticated]
    #permission_classes = [AllowAny]

    def dispatch(self, request, *args, **kwargs):
        print(f"DEBUG: Request to VideoListView")
        print(f"DEBUG: Authentication classes: {self.authentication_classes}")
        print(f"DEBUG: Cookies in request: {list(request.COOKIES.keys())}")
        return super().dispatch(request, *args, **kwargs)
