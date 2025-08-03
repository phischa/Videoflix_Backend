import pytest
from unittest.mock import patch, ANY
from django.core.files.uploadedfile import SimpleUploadedFile
from video_app.models import Video


@pytest.mark.django_db
def test_video_post_save_signal_created():
    """Test video post_save signal when video is created"""
    with patch('video_app.signals.logger') as mock_logger, \
        patch('video_app.signals.queue_video_processing') as mock_queue:
        
        # Create video without file (should not trigger processing)
        video = Video.objects.create(title="New Video", category="action")
        
        # Should log the creation (use ANY for ID since it's auto-generated)
        mock_logger.debug.assert_called()
        mock_logger.info.assert_called_with(
            "New Video created without file: %s (ID: %s)", 
            "New Video", video.id
        )
        # Should not queue processing (no file)
        mock_queue.assert_not_called()


@pytest.mark.django_db  
def test_video_post_save_signal_updated():
    """Test video post_save signal when video is updated"""
    video = Video.objects.create(title="Test Video", category="action")
    
    with patch('video_app.signals.logger') as mock_logger:
        video.title = "Updated Title"
        video.save()
        
        # Should log the update
        mock_logger.debug.assert_called_with(
            "Existing Video updated: %s (ID: %s)", 
            "Updated Title", video.id
        )


@pytest.mark.django_db
def test_video_post_save_signal_with_file():
    """Test video post_save signal when video is created with file"""
    with patch('video_app.signals.logger') as mock_logger, \
        patch('video_app.signals.queue_video_processing') as mock_queue:
        
        # Create a proper mock file
        mock_file = SimpleUploadedFile(
            name='test_video.mp4',
            content=b'fake video content',
            content_type='video/mp4'
        )
        
        # Create video with file (should trigger processing)
        video = Video.objects.create(
            title="Video with File", 
            category="action",
            original_file=mock_file
        )
        
        # Should log and queue processing
        mock_logger.info.assert_called_with(
            "New Video created with file: %s (ID: %s). Starting background processing", 
            "Video with File", video.id
        )
        mock_queue.assert_called_once_with(video.id)