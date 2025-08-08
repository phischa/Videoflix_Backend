from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    """
    Configuration class for the video app.
    
    Handles video streaming functionality including HLS processing,
    file uploads, and video metadata management.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video_app'

    def ready(self):
        """
        Called when app is fully loaded.
        
        Imports signal handlers for video processing automation.
        """
        import video_app.signals