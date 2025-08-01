import os
import subprocess
from django.conf import settings
from .models import Video

def process_video_to_hls(video_id):
    """
    Background job: Convert video to HLS with multiple resolutions
    """
    try:
        video = Video.object.get(id=video_id)
        video.processing_status = 'processing'
        video.proseccing_progress = 0
        video.save()

    except Exception as e:
        video.processing_status = 'failed'
        video.processing_error = str(e)
        video.save()