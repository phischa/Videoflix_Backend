from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from .utils import validate_file_size


GENRE_CHOICES = [
    ('action', 'Action'),
    ('drama', 'Drama'),
    ('comedy', 'Comedy'),
    ('romance', 'Romance'),
    ('thriller', 'Thriller'),
    ('documentary', 'Documentary'),
    ('animation', 'Animation'),
]

PROCESSING_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing', 'Processing'), 
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]


class Video(models.Model):
    """
    Video model for HLS streaming platform.
    
    Manages video metadata, upload files, processing status 
    and HLS streaming information.
    """
    
    title = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=GENRE_CHOICES, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    original_file = models.FileField(
        upload_to='videos/original/',
        validators=[
            FileExtensionValidator(allowed_extensions=['mp4', 'mov', 'avi', 'wmv', 'asf']),
            validate_file_size
        ],
        help_text="Original video file for processing (Max: 10GB)"
    )
    processing_status = models.CharField(
        max_length=20, 
        choices=PROCESSING_STATUS_CHOICES, 
        default='pending', 
        db_index=True
    )
    processing_progress = models.PositiveIntegerField(
        default=0, 
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        help_text="Processing progress in %"
    )
    processing_error = models.TextField(
        blank=True, 
        null=True,
        help_text="Error message if processing failed"
    )
    hls_directory = models.CharField(
        max_length=500,
        blank=True,
        null=True, 
        help_text="Path to HLS files directory"
    )  
    duration_seconds = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Video duration in seconds"
    )
    file_size_mb = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Original file size in MB"
    )

    class Meta:
        """Meta options for Video model."""
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'created_at']),
        ]

    def __str__(self):
        """String representation of Video object."""
        return f"{self.title} ({self.get_category_display()})"

    @property
    def thumbnail_url(self):
        """Returns the full URL for the thumbnail"""
        if self.thumbnail:
            return self.thumbnail.url
        return None
        