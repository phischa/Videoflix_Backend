import logging
from .models import Video
from .tasks import queue_video_processing
from django.dispatch import receiver
from django.db.models.signals import post_save

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    Signal: Auto-queue video for HLS processing when uploaded
    """
    logger.debug("Video post_save signal received for video %s: %s", 
                instance.id, instance.title)
    
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
