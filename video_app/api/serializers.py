from rest_framework import serializers
from video_app.models import Video


class VideoListSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.ReadOnlyField()

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']