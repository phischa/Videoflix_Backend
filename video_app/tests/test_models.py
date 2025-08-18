import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from video_app.models import Video, GENRE_CHOICES, PROCESSING_STATUS_CHOICES


@pytest.mark.django_db
def test_video_creation_success():
    """Test successful video creation with all required fields"""
    video = Video.objects.create(
        title="Test Video",
        description="This is a test video",
        category="action"
    )
    
    # Test that video was created
    assert isinstance(video, Video)
    assert video.title == "Test Video"
    assert video.description == "This is a test video"
    assert video.category == "action"
    assert video.processing_status == "pending"  # default value
    assert video.processing_progress == 0  # default value
    
    # Test string representation
    assert str(video) == "Test Video (Action)"


@pytest.mark.django_db        
def test_video_choices_constants():
    """Test that choice constants are properly defined"""
    # Test GENRE_CHOICES
    genre_values = [choice[0] for choice in GENRE_CHOICES]
    assert 'action' in genre_values
    assert 'drama' in genre_values
    assert 'comedy' in genre_values
    
    # Test PROCESSING_STATUS_CHOICES
    status_values = [choice[0] for choice in PROCESSING_STATUS_CHOICES]
    assert 'pending' in status_values
    assert 'processing' in status_values
    assert 'completed' in status_values
    assert 'failed' in status_values


@pytest.mark.django_db
def test_video_thumbnail_url_property():
    """Test thumbnail_url property"""
    video = Video.objects.create(
        title="Test Video",
        category="action"
    )
    
    # Without thumbnail should return None
    assert video.thumbnail_url is None


@pytest.mark.django_db
def test_video_default_values():
    """Test that default values are set correctly"""
    video = Video.objects.create(
        title="Test Video",
        category="action"
    )
    
    assert video.processing_status == 'pending'
    assert video.processing_progress == 0
    assert video.description == ''


@pytest.mark.django_db
def test_video_meta_ordering():
    """Test that videos are ordered by created_at descending"""
    video1 = Video.objects.create(title="First Video", category="action")
    video2 = Video.objects.create(title="Second Video", category="drama")
    
    videos = Video.objects.all()
    assert videos[0] == video2  # Newest first
    assert videos[1] == video1


@pytest.fixture
@pytest.mark.django_db
def test_user():
    """Fixture to create a test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )