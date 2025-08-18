import os
import shutil
import logging
from .models import Video
from .tasks import queue_video_processing
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    Signal: Auto-queue video for HLS processing when uploaded
    """
    if created and instance.original_file:
        logger.info("New Video created with file: %s (ID: %s). Starting background processing", 
                    instance.title, instance.id)
        
        try:
            # Queue the video for background processing
            job_id = queue_video_processing(instance.id)
            logger.info("Background job queued for video %s with job ID: %s", 
                        instance.id, job_id)
        except Exception as e:
            logger.error("Failed to queue background job for video %s: %s", 
                        instance.id, str(e), exc_info=True)
            # Set video status to failed if queueing fails
            instance.processing_status = 'failed'
            instance.processing_error = f"Failed to queue processing job: {str(e)}"
            instance.save()
            
    elif created:
        logger.info("New Video created without file: %s (ID: %s)", 
                    instance.title, instance.id)
    else:
        logger.debug("Existing Video updated: %s (ID: %s)", 
                    instance.title, instance.id)

@receiver(post_delete, sender=Video)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes all files from filesystem when Video object is deleted:
    - Original video file
    - Complete HLS directory with all resolutions and segments
    - Thumbnail image
    """
    logger.info("Deleting files for video: %s (ID: %s)", instance.title, instance.id)
    
    # 1. Delete original video file
    if instance.original_file:
        try:
            if os.path.isfile(instance.original_file.path):
                os.remove(instance.original_file.path)
                logger.info("Original file deleted: %s", instance.original_file.path)
        except Exception as e:
            logger.error("Failed to delete original file %s: %s", 
                        instance.original_file.path, str(e))
    
    # 2. Delete complete HLS directory (all resolutions and segments)
    if instance.hls_directory:
        try:
            if os.path.exists(instance.hls_directory):
                shutil.rmtree(instance.hls_directory)
                logger.info("HLS directory deleted: %s", instance.hls_directory)
        except Exception as e:
            logger.error("Failed to delete HLS directory %s: %s", 
                        instance.hls_directory, str(e))
    else:
        # Fallback: Try to delete using standard path pattern
        hls_fallback_path = f"media/hls/{instance.id}/"
        try:
            if os.path.exists(hls_fallback_path):
                shutil.rmtree(hls_fallback_path)
                logger.info("HLS directory deleted (fallback): %s", hls_fallback_path)
        except Exception as e:
            logger.error("Failed to delete HLS directory (fallback) %s: %s", 
                        hls_fallback_path, str(e))
    
    # 3. Delete thumbnail
    if instance.thumbnail:
        try:
            if os.path.isfile(instance.thumbnail.path):
                os.remove(instance.thumbnail.path)
                logger.info("Thumbnail deleted: %s", instance.thumbnail.path)
        except Exception as e:
            logger.error("Failed to delete thumbnail %s: %s", 
                        instance.thumbnail.path, str(e))
    
    logger.info("File deletion completed for video: %s (ID: %s)", instance.title, instance.id)
