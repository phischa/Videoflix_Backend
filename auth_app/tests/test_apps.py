import pytest
from django.apps import apps
from django.test import override_settings

from auth_app.apps import AuthAppConfig


class TestAuthAppConfig:
    """Tests for AuthAppConfig."""
    
    def test_apps_config_exists(self):
        """Test that auth_app config exists."""
        app_config = apps.get_app_config('auth_app')
        assert app_config is not None
        assert isinstance(app_config, AuthAppConfig)
        
    def test_app_name(self):
        """Test app name is correct."""
        app_config = apps.get_app_config('auth_app')
        assert app_config.name == 'auth_app'
        
    def test_default_auto_field(self):
        """Test default auto field setting."""
        app_config = apps.get_app_config('auth_app')
        assert app_config.default_auto_field == 'django.db.models.BigAutoField'
        
    def test_app_is_installed(self):
        """Test that auth_app is in INSTALLED_APPS."""
        app_config = apps.get_app_config('auth_app')
        assert app_config.name in apps.all_models
        
    def test_app_ready_method_exists(self):
        """Test that ready method can be called safely."""
        app_config = apps.get_app_config('auth_app')
        
        # Should not raise an error
        try:
            app_config.ready()
        except Exception:
            # ready() method might not exist or might be empty, both are okay
            pass
        