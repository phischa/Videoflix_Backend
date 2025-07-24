from rest_framework import serializers
from .models import Video


class VideoListSerializer(serializers.Serializer):
    thumbnail_url = serializers.ReadOnlyField()

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']