from rest_framework import serializers
from video_app.models import Video


class VideoListSerializer(serializers.ModelSerializer):
    """
    Serializer for video list API.
    
    Provides basic video information with absolute thumbnail URLs
    for displaying videos in list views.
    """
    thumbnail_url = serializers.SerializerMethodField() 

    class Meta:
        """Meta configuration for VideoListSerializer."""
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']

    def get_thumbnail_url(self, obj):
        """Return absolute URL for thumbnail"""
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
        return None
        