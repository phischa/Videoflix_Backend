import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from django.core.files.uploadedfile import SimpleUploadedFile
from video_app.models import Video, GENRE_CHOICES
from video_app.api.serializers import VideoListSerializer


@pytest.fixture
@pytest.mark.django_db
def sample_video():
    """Create a sample video for testing"""
    return Video.objects.create(
        title="Test Movie",
        description="A great test movie",
        category="action"
    )


@pytest.fixture
@pytest.mark.django_db
def video_with_thumbnail():
    """Create a video with thumbnail for testing"""
    # Create a mock thumbnail file
    thumbnail_content = b"fake image content"
    thumbnail_file = SimpleUploadedFile("test_thumb.jpg", thumbnail_content, content_type="image/jpeg")
    
    return Video.objects.create(
        title="Movie with Thumbnail",
        description="Movie that has a thumbnail",
        category="drama",
        thumbnail=thumbnail_file
    )


@pytest.mark.django_db
class TestVideoListSerializer:
    """Test VideoListSerializer functionality"""
    
    def test_serializer_fields_included(self, sample_video):
        """Test that all expected fields are included in serialization"""
        serializer = VideoListSerializer(sample_video)
        data = serializer.data
        
        expected_fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']
        
        # Check all expected fields are present
        for field in expected_fields:
            assert field in data, f"Field '{field}' missing from serialized data"
    
    def test_serializer_fields_excluded(self, sample_video):
        """Test that sensitive/unnecessary fields are excluded"""
        serializer = VideoListSerializer(sample_video)
        data = serializer.data
        
        excluded_fields = [
            'processing_status', 'processing_progress', 'processing_error',
            'hls_directory', 'duration_seconds', 'file_size_mb', 'original_file'
        ]
        
        # Check excluded fields are not present
        for field in excluded_fields:
            assert field not in data, f"Field '{field}' should not be in serialized data"
    
    def test_serialize_video_basic_data(self, sample_video):
        """Test basic video data serialization"""
        serializer = VideoListSerializer(sample_video)
        data = serializer.data
        
        assert data['id'] == sample_video.id
        assert data['title'] == "Test Movie"
        assert data['description'] == "A great test movie"
        assert data['category'] == "action"
        assert 'created_at' in data
        assert isinstance(data['created_at'], str)  # Should be ISO format string
    
    def test_serialize_thumbnail_url_none(self, sample_video):
        """Test thumbnail_url serialization when no thumbnail exists"""
        serializer = VideoListSerializer(sample_video)
        data = serializer.data
        
        assert data['thumbnail_url'] is None
    
    def test_serialize_thumbnail_url_with_file(self, video_with_thumbnail):
        """Test thumbnail_url serialization when thumbnail exists"""
        serializer = VideoListSerializer(video_with_thumbnail)
        data = serializer.data
        
        # Should have thumbnail URL
        assert data['thumbnail_url'] is not None
        assert isinstance(data['thumbnail_url'], str)
        assert 'test_thumb' in data['thumbnail_url']
    
    def test_serialize_created_at_format(self, sample_video):
        """Test that created_at is properly formatted"""
        serializer = VideoListSerializer(sample_video)
        data = serializer.data
        
        # Should be ISO format string
        created_at = data['created_at']
        assert isinstance(created_at, str)
        
        # Should be parseable back to datetime
        try:
            datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("created_at is not in valid ISO format")
    
    def test_deserialize_valid_data(self):
        """Test deserialization with valid data"""
        valid_data = {
            'title': 'New Video',
            'description': 'A new video description',
            'category': 'comedy'
        }
        
        serializer = VideoListSerializer(data=valid_data)
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        
        # Check validated data
        validated_data = serializer.validated_data
        assert validated_data['title'] == 'New Video'
        assert validated_data['description'] == 'A new video description'
        assert validated_data['category'] == 'comedy'
    
    def test_deserialize_invalid_category(self):
        """Test deserialization with invalid category"""
        invalid_data = {
            'title': 'New Video',
            'description': 'A new video description',
            'category': 'invalid_category'
        }
        
        serializer = VideoListSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'category' in serializer.errors
    
    def test_deserialize_missing_required_fields(self):
        """Test deserialization with missing required fields"""
        incomplete_data = {
            'description': 'Missing title and category'
        }
        
        serializer = VideoListSerializer(data=incomplete_data)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
        assert 'category' in serializer.errors
    
    def test_deserialize_empty_title(self):
        """Test deserialization with empty title"""
        invalid_data = {
            'title': '',
            'description': 'Valid description',
            'category': 'action'
        }
        
        serializer = VideoListSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
    
    def test_deserialize_title_too_long(self):
        """Test deserialization with title exceeding max length"""
        invalid_data = {
            'title': 'x' * 101,  # Assuming max_length=100 in model
            'description': 'Valid description',
            'category': 'action'
        }
        
        serializer = VideoListSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
    
    def test_thumbnail_url_readonly(self):
        """Test that thumbnail_url is read-only"""
        data_with_thumbnail_url = {
            'title': 'New Video',
            'description': 'Description',
            'category': 'action',
            'thumbnail_url': 'http://example.com/fake.jpg'  # Should be ignored
        }
        
        serializer = VideoListSerializer(data=data_with_thumbnail_url)
        assert serializer.is_valid()
        
        # thumbnail_url should not be in validated_data
        assert 'thumbnail_url' not in serializer.validated_data
    
    def test_create_video_from_serializer(self):
        """Test creating a video through serializer"""
        valid_data = {
            'title': 'Created Video',
            'description': 'Video created through serializer',
            'category': 'romance'
        }
        
        serializer = VideoListSerializer(data=valid_data)
        assert serializer.is_valid()
        
        video = serializer.save()
        assert isinstance(video, Video)
        assert video.title == 'Created Video'
        assert video.description == 'Video created through serializer'
        assert video.category == 'romance'
        assert video.processing_status == 'pending'  # Default value


@pytest.mark.django_db
class TestVideoListSerializerEdgeCases:
    """Test edge cases and advanced scenarios"""
    
    def test_serialize_multiple_videos(self):
        """Test serializing multiple videos"""
        videos = [
            Video.objects.create(title="Video 1", category="action"),
            Video.objects.create(title="Video 2", category="drama"),
            Video.objects.create(title="Video 3", category="comedy")
        ]
        
        serializer = VideoListSerializer(videos, many=True)
        data = serializer.data
        
        assert len(data) == 3
        assert data[0]['title'] == "Video 1"
        assert data[1]['title'] == "Video 2"
        assert data[2]['title'] == "Video 3"
    
    def test_partial_update_serialization(self, sample_video):
        """Test partial update with serializer"""
        update_data = {
            'title': 'Updated Title'
        }
        
        serializer = VideoListSerializer(sample_video, data=update_data, partial=True)
        assert serializer.is_valid()
        
        updated_video = serializer.save()
        assert updated_video.title == 'Updated Title'
        assert updated_video.description == sample_video.description  # Unchanged
        assert updated_video.category == sample_video.category  # Unchanged
    
    def test_serialize_with_unicode_characters(self):
        """Test serialization with unicode characters"""
        unicode_video = Video.objects.create(
            title="Αἰσχύλος Movie 🎬",  # Greek and emoji
            description="A movie with unicode: 中文, العربية, русский",
            category="documentary"
        )
        
        serializer = VideoListSerializer(unicode_video)
        data = serializer.data
        
        assert data['title'] == "Αἰσχύλος Movie 🎬"
        assert "中文" in data['description']
        assert "العربية" in data['description']
        assert "русский" in data['description']
    
    def test_validate_all_genre_choices(self):
        """Test that all valid genre choices work"""
        for genre_code, genre_display in GENRE_CHOICES:
            valid_data = {
                'title': f'{genre_display} Movie',
                'description': f'A {genre_display.lower()} movie',
                'category': genre_code
            }
            
            serializer = VideoListSerializer(data=valid_data)
            assert serializer.is_valid(), f"Genre '{genre_code}' should be valid. Errors: {serializer.errors}"
    
    def test_serializer_performance_with_large_description(self):
        """Test serializer with very large description"""
        large_description = "Lorem ipsum " * 1000  # Large text
        
        video = Video.objects.create(
            title="Performance Test",
            description=large_description,
            category="documentary"
        )
        
        serializer = VideoListSerializer(video)
        data = serializer.data
        
        assert len(data['description']) == len(large_description)
        assert data['description'] == large_description


@pytest.mark.django_db
class TestVideoListSerializerValidation:
    """Test custom validation logic"""
    
    def test_case_sensitive_category_validation(self):
        """Test that category validation is case sensitive"""
        invalid_data = {
            'title': 'Test Movie',
            'description': 'Test description',
            'category': 'ACTION'  # Should be 'action' (lowercase)
        }
        
        serializer = VideoListSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'category' in serializer.errors
    
    def test_whitespace_handling(self):
        """Test handling of whitespace in fields"""
        data_with_whitespace = {
            'title': '  Test Movie  ',
            'description': '  A movie with leading/trailing spaces  ',
            'category': 'action'
        }
        
        serializer = VideoListSerializer(data=data_with_whitespace)
        assert serializer.is_valid()
        
        # Django typically doesn't auto-strip whitespace unless configured
        validated_data = serializer.validated_data
        assert validated_data['title'] == '  Test Movie  '
        assert validated_data['description'] == '  A movie with leading/trailing spaces  '
        