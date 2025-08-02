import os
import subprocess
from django.conf import settings
from .models import Video

def process_video_to_hls(video_id):
    """
    Background job: Convert video to HLS with multiple resolutions
    """
    try:
        video = Video.objects.get(id=video_id)
        video.processing_status = 'processing'
        video.prosessing_progress = 0
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
        print(f"Error: Video with ID {video_id} not found")
    except Exception as e:
        if video:
            video.processing_status = 'failed'
            video.processing_error = str(e)
            video.save()
        print(f"Error processing video {video_id}: {str(e)}")


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
    
    # Run FFmpeg
    subprocess.run(ffmpeg_cmd, check=True, capture_output=True)


def extract_video_metadata(video, input_path):
    """
    Extract video duration and file size using FFprobe
    """
    # Get video duration with ffprobe
    duration_cmd = [
        'ffprobe', 
        '-v', 'quiet',
        '-show_entries', 'format=duration',
        '-of', 'csv=p=0',
        input_path
    ]
    
    result = subprocess.run(duration_cmd, capture_output=True, text=True)
    duration = float(result.stdout.strip())
    
    # Get file size
    file_size_bytes = os.path.getsize(input_path)
    file_size_mb = file_size_bytes // (1024 * 1024)
    
    # Update video model
    video.duration_seconds = int(duration)
    video.file_size_mb = file_size_mb
    video.save()