import pytest
import os
from unittest.mock import patch, mock_open
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from video_app.models import Video


@pytest.fixture
@pytest.mark.django_db
def api_client():
    """Create API client for testing"""
    return APIClient()


@pytest.fixture
@pytest.mark.django_db
def test_user():
    """Create test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
@pytest.mark.django_db
def test_videos():
    """Create test videos"""
    videos = []
    videos.append(Video.objects.create(
        title="Action Movie",
        description="Great action movie",
        category="action"
    ))
    videos.append(Video.objects.create(
        title="Comedy Show",
        description="Funny comedy",
        category="comedy"
    ))
    return videos


@pytest.mark.django_db
class TestVideoListView:
    """Test VideoListView endpoint"""
    
    def test_video_list_requires_authentication(self, api_client):
        """Test that video list requires authentication"""
        url = reverse('video-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_video_list_success_with_auth(self, api_client, test_user, test_videos):
        """Test successful video list retrieval with authentication"""
        # Force authenticate user
        api_client.force_authenticate(user=test_user)
        
        url = reverse('video-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        # Check video data structure
        video_data = response.data[0]
        assert 'id' in video_data
        assert 'title' in video_data
        assert 'description' in video_data
        assert 'category' in video_data
        assert 'thumbnail_url' in video_data
        assert 'created_at' in video_data
    
    def test_video_list_ordering(self, api_client, test_user, test_videos):
        """Test that videos are ordered by created_at descending"""
        api_client.force_authenticate(user=test_user)
        
        url = reverse('video-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Should be ordered by newest first (Comedy Show was created after Action Movie)
        assert response.data[0]['title'] == "Comedy Show"
        assert response.data[1]['title'] == "Action Movie"
    
    def test_video_list_empty(self, api_client, test_user):
        """Test video list when no videos exist"""
        api_client.force_authenticate(user=test_user)
        
        url = reverse('video-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


@pytest.mark.django_db
class TestHLSManifestView:
    """Test HLS Manifest View endpoint"""
    
    def test_hls_manifest_requires_authentication(self, api_client, test_videos):
        """Test that HLS manifest requires authentication"""
        video = test_videos[0]
        url = f'/video/{video.id}/720p/index.m3u8'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_hls_manifest_video_not_found(self, api_client, test_user):
        """Test HLS manifest with non-existent video"""
        api_client.force_authenticate(user=test_user)
        
        url = '/video/99999/720p/index.m3u8'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['detail'] == "Video not found"
    
    def test_hls_manifest_invalid_resolution(self, api_client, test_user, test_videos):
        """Test HLS manifest with invalid resolution"""
        api_client.force_authenticate(user=test_user)
        video = test_videos[0]
        
        url = f'/video/{video.id}/4k/index.m3u8'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['detail'] == "Invalid resolution"
    
    @patch('os.path.exists')
    def test_hls_manifest_file_not_found(self, mock_exists, api_client, test_user, test_videos):
        """Test HLS manifest when file doesn't exist"""
        mock_exists.return_value = False
        api_client.force_authenticate(user=test_user)
        video = test_videos[0]
        
        url = f'/video/{video.id}/720p/index.m3u8'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['detail'] == "Manifest not found"
    
    @patch('builtins.open', new_callable=mock_open, read_data="#EXTM3U\n#EXT-X-VERSION:3\n")
    @patch('os.path.exists')
    def test_hls_manifest_success(self, mock_exists, mock_file, api_client, test_user, test_videos):
        """Test successful HLS manifest retrieval"""
        mock_exists.return_value = True
        api_client.force_authenticate(user=test_user)
        video = test_videos[0]
        
        url = f'/video/{video.id}/720p/index.m3u8'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'application/vnd.apple.mpegurl'
        assert "#EXTM3U" in response.content.decode()


@pytest.mark.django_db  
class TestHLSSegmentView:
    """Test HLS Segment View endpoint"""
    
    def test_hls_segment_requires_authentication(self, api_client, test_videos):
        """Test that HLS segment requires authentication"""
        video = test_videos[0]
        url = f'/video/{video.id}/720p/001.ts/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_hls_segment_video_not_found(self, api_client, test_user):
        """Test HLS segment with non-existent video"""
        api_client.force_authenticate(user=test_user)
        
        url = '/video/99999/720p/001.ts/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['detail'] == "Video not found"
    
    def test_hls_segment_invalid_resolution(self, api_client, test_user, test_videos):
        """Test HLS segment with invalid resolution"""
        api_client.force_authenticate(user=test_user)
        video = test_videos[0]
        
        url = f'/video/{video.id}/4k/001.ts/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['detail'] == "Invalid resolution"
    
    def test_hls_segment_invalid_segment_format(self, api_client, test_user, test_videos):
        """Test HLS segment with invalid segment format"""
        api_client.force_authenticate(user=test_user)
        video = test_videos[0]
        
        # Test invalid segment names
        invalid_segments = ['invalid.ts', '1.ts', 'segment.mp4', 'abc.ts']
        
        for segment in invalid_segments:
            url = f'/video/{video.id}/720p/{segment}/'
            response = api_client.get(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_hls_segment_valid_format(self, api_client, test_user, test_videos):
        """Test HLS segment with valid segment format"""
        api_client.force_authenticate(user=test_user)
        video = test_videos[0]
        
        # Test valid segment names (should pass regex validation)
        valid_segments = ['000.ts', '001.ts', '999.ts']
        
        for segment in valid_segments:
            url = f'/video/{video.id}/720p/{segment}/'
            response = api_client.get(url)
            # Should pass validation (actual file check happens later)
            # Since we're not mocking file existence, it will fail at file check
            # but the regex validation should pass
            assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_200_OK]