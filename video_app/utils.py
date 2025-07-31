from django.conf import settings
from django.core.exceptions import ValidationError

def validate_file_size(value):
    """Validates that uploaded file doesn't exceed MAX_FILE_SIZE"""
    if value.size > settings.MAX_FILE_SIZE:
        raise ValidationError("File size cannot exceed 10GB")