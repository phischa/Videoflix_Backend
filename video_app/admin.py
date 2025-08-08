from django.contrib import admin
from .models import Video


@admin.register(Video)  
class VideoAdmin(admin.ModelAdmin):
    """
    Django admin configuration for Video model.
    
    Provides interface for managing videos with filtering,
    searching, and read-only processing fields.
    """
    list_display = ['title', 'category', 'processing_status', 'created_at']
    list_filter = ['processing_status', 'category', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['processing_progress', 'processing_error', 'hls_directory', 'duration_seconds', 'file_size_mb']
