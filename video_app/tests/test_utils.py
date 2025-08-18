import pytest
from unittest.mock import Mock, patch
from django.core.exceptions import ValidationError
from django.test import override_settings
from video_app.utils import validate_file_size


class TestValidateFileSize:
    """Test validate_file_size utility function"""
    
    def create_mock_file(self, size_in_bytes):
        """Helper method to create mock file with specific size"""
        mock_file = Mock()
        mock_file.size = size_in_bytes
        return mock_file
    
    @override_settings(MAX_FILE_SIZE=10737418240)  # 10GB in bytes
    def test_validate_file_size_success_small_file(self):
        """Test validation passes for small files"""
        # Create file that's 1MB (well under 10GB limit)
        small_file = self.create_mock_file(1024 * 1024)  # 1MB
        
        # Should not raise ValidationError
        try:
            validate_file_size(small_file)
        except ValidationError:
            pytest.fail("validate_file_size raised ValidationError for valid small file")
    
    @override_settings(MAX_FILE_SIZE=10737418240)  # 10GB in bytes
    def test_validate_file_size_success_medium_file(self):
        """Test validation passes for medium files"""
        # Create file that's 1GB (under 10GB limit)
        medium_file = self.create_mock_file(1073741824)  # 1GB
        
        # Should not raise ValidationError
        try:
            validate_file_size(medium_file)
        except ValidationError:
            pytest.fail("validate_file_size raised ValidationError for valid medium file")
    
    @override_settings(MAX_FILE_SIZE=10737418240)  # 10GB in bytes
    def test_validate_file_size_success_at_limit(self):
        """Test validation passes for file exactly at size limit"""
        # Create file that's exactly 10GB
        limit_file = self.create_mock_file(10737418240)  # 10GB exactly
        
        # Should not raise ValidationError
        try:
            validate_file_size(limit_file)
        except ValidationError:
            pytest.fail("validate_file_size raised ValidationError for file at exact limit")
    
    @override_settings(MAX_FILE_SIZE=10737418240)  # 10GB in bytes
    def test_validate_file_size_fail_over_limit(self):
        """Test validation fails for files over size limit"""
        # Create file that's over 10GB
        large_file = self.create_mock_file(10737418241)  # 10GB + 1 byte
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(large_file)
        
        assert "File size cannot exceed 10GB" in str(exc_info.value)
    
    @override_settings(MAX_FILE_SIZE=10737418240)  # 10GB in bytes
    def test_validate_file_size_fail_way_over_limit(self):
        """Test validation fails for files way over size limit"""
        # Create file that's 20GB (double the limit)
        huge_file = self.create_mock_file(21474836480)  # 20GB
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(huge_file)
        
        assert "File size cannot exceed 10GB" in str(exc_info.value)
    
    @override_settings(MAX_FILE_SIZE=1048576)  # 1MB for testing
    def test_validate_file_size_different_max_size(self):
        """Test validation with different MAX_FILE_SIZE setting"""
        # Create file that's 2MB (over 1MB limit)
        file_2mb = self.create_mock_file(2097152)  # 2MB
        
        # Should raise ValidationError with 1MB limit
        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(file_2mb)
        
        assert "File size cannot exceed 10GB" in str(exc_info.value)
    
    def test_validate_file_size_zero_byte_file(self):
        """Test validation passes for zero-byte files"""
        # Create empty file
        empty_file = self.create_mock_file(0)
        
        # Should not raise ValidationError (empty files are valid)
        try:
            validate_file_size(empty_file)
        except ValidationError:
            pytest.fail("validate_file_size raised ValidationError for empty file")
    
    @patch('video_app.utils.settings.MAX_FILE_SIZE', 5368709120)  # 5GB
    def test_validate_file_size_with_mocked_settings(self):
        """Test validation with mocked settings"""
        # Create file that's 6GB (over 5GB mocked limit)
        large_file = self.create_mock_file(6442450944)  # 6GB
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(large_file)
        
        assert "File size cannot exceed 10GB" in str(exc_info.value)
    
    def test_validate_file_size_file_without_size_attribute(self):
        """Test validation handles files without size attribute gracefully"""
        # Create mock file without size attribute
        invalid_file = Mock(spec=[])  # Mock with no attributes
        
        # Should raise AttributeError when trying to access .size
        with pytest.raises(AttributeError):
            validate_file_size(invalid_file)
    
    def test_validate_file_size_file_with_none_size(self):
        """Test validation handles files with None size"""
        # Create mock file with None size
        none_size_file = Mock()
        none_size_file.size = None
        
        # Should raise TypeError when comparing None > MAX_FILE_SIZE
        with pytest.raises(TypeError):
            validate_file_size(none_size_file)
    
    def test_validate_file_size_file_with_negative_size(self):
        """Test validation handles files with negative size"""
        # Create mock file with negative size (shouldn't happen in reality)
        negative_file = self.create_mock_file(-1)
        
        # Should not raise ValidationError (negative < MAX_FILE_SIZE)
        try:
            validate_file_size(negative_file)
        except ValidationError:
            pytest.fail("validate_file_size raised ValidationError for negative size file")


class TestUtilsIntegration:
    """Integration tests for utils with real file-like objects"""
    
    def test_validate_file_size_with_uploadedfile_mock(self):
        """Test with Django UploadedFile-like mock"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create a small uploaded file
        small_content = b"Small file content"
        uploaded_file = SimpleUploadedFile("test.txt", small_content)
        
        # Should not raise ValidationError
        try:
            validate_file_size(uploaded_file)
        except ValidationError:
            pytest.fail("validate_file_size raised ValidationError for small uploaded file")
    
    @override_settings(MAX_FILE_SIZE=10)  # Very small limit for testing
    def test_validate_file_size_with_uploadedfile_over_limit(self):
        """Test with Django UploadedFile that exceeds limit"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create file larger than 10 bytes
        large_content = b"This content is definitely larger than 10 bytes"
        uploaded_file = SimpleUploadedFile("large_test.txt", large_content)
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(uploaded_file)
        
        assert "File size cannot exceed 10GB" in str(exc_info.value)


class TestUtilsConstants:
    """Test utils constants and imports"""
    
    def test_imports_are_available(self):
        """Test that required imports are available"""
        from video_app.utils import validate_file_size
        from django.conf import settings
        from django.core.exceptions import ValidationError
        
        # If we get here, imports work
        assert callable(validate_file_size)
    
    def test_settings_max_file_size_exists(self):
        """Test that MAX_FILE_SIZE setting exists"""
        from django.conf import settings
        
        # Should have MAX_FILE_SIZE setting
        assert hasattr(settings, 'MAX_FILE_SIZE')
        assert isinstance(settings.MAX_FILE_SIZE, int)
        assert settings.MAX_FILE_SIZE > 0