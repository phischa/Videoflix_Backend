import os
import subprocess
import logging
import django_rq
from django.conf import settings
from .models import Video

logger = logging.getLogger(__name__)

def queue_video_processing(video_id):
    """
    Enqueue video processing job in Redis Queue
    Call this from Views/Signals to start background processing
    """
    try:
        queue = django_rq.get_queue('default')
        job = queue.enqueue(
            process_video_to_hls,
            video_id,
            job_timeout=1800
        )
        logger.info("Video %s queued for processing. Job ID: %s", video_id, job.id)
        return job.id
    except Exception as e:
        logger.error("Failed to queue video %s for processing: %s", video_id, str(e))
        raise

def process_video_to_hls(video_id):
    """
    Background job: Convert video to HLS with multiple resolutions
    """
    try:
        video = Video.objects.get(id=video_id)
        video.processing_status = 'processing'
        video.processing_progress = 0
        video.save()

        # File paths
        input_path = video.original_file.path
        output_dir = f"media/hls/{video.id}/"

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        video.hls_directory = output_dir
        video.save()

        # Resolutions to generate
        resolutions = [
            {'name': '120p', 'height': 120, 'bitrate': '200k'},
            {'name': '360p', 'height': 360, 'bitrate': '800k'}, 
            {'name': '720p', 'height': 720, 'bitrate': '2500k'},
            {'name': '1080p', 'height': 1080, 'bitrate': '5000k'},
        ]

        for i, res in enumerate(resolutions):
            process_resolution(input_path, output_dir, res)
            
            # Update progress (25% per resolution)
            progress = int((i + 1) / len(resolutions) * 100)
            video.processing_progress = progress
            video.save()
        
        # Extract metadata
        extract_video_metadata(video, input_path)
        
        video.processing_status = 'completed'
        video.save()

    except Video.DoesNotExist:
        error_msg = f"Video with ID {video_id} not found"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Error processing video {video_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        if video:
            video.processing_status = 'failed'
            video.processing_error = str(e)
            video.save()
        raise e


def process_resolution(input_path, output_dir, resolution):
    """
    Convert video to specific resolution with HLS segmentation
    """
    res_name = resolution['name']
    height = resolution['height'] 
    bitrate = resolution['bitrate']
    
    # Output directory for this resolution
    res_output_dir = os.path.join(output_dir, res_name)
    os.makedirs(res_output_dir, exist_ok=True)
    
    # Output files
    playlist_path = os.path.join(res_output_dir, 'index.m3u8')
    segment_pattern = os.path.join(res_output_dir, '%03d.ts')
    
    # FFmpeg command for HLS conversion
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', input_path,                    # Input file
        '-vf', f'scale=-2:{height}',         # Scale to resolution
        '-c:v', 'libx264',                   # Video codec
        '-b:v', bitrate,                     # Video bitrate
        '-c:a', 'aac',                       # Audio codec
        '-b:a', '128k',                      # Audio bitrate
        '-hls_time', '10',                   # 10-second segments
        '-hls_list_size', '0',               # Keep all segments
        '-f', 'hls',                         # HLS format
        playlist_path                        # Output playlist
    ]
    
    try:
        # Run FFmpeg
        result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        logger.debug("FFmpeg conversion to %s completed successfully", res_name)
    except subprocess.CalledProcessError as e:
        logger.error("FFmpeg failed for resolution %s: %s", res_name, e.stderr)
        raise



def extract_video_metadata(video, input_path):
    """
    Extract video duration and file size using FFprobe
    """
    # Get video duration with ffprobe
    try:
        duration_cmd = [
            'ffprobe', 
            '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            input_path
        ]
        
        result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        
        # Get file size
        file_size_bytes = os.path.getsize(input_path)
        file_size_mb = file_size_bytes // (1024 * 1024)
        
        # Update video model
        video.duration_seconds = int(duration)
        video.file_size_mb = file_size_mb
        video.save()
        
        logger.info("Metadata extracted for video %s: %ds, %dMB", 
                    video.id, int(duration), file_size_mb)
    except subprocess.CalledProcessError as e:
        logger.error("FFprobe failed for video %s: %s", video.id, e.stderr)
        raise
    except Exception as e:
        logger.error("Failed to extract metadata for video %s: %s", video.id, str(e))
        raise