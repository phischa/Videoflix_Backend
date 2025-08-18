from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    """
    Configuration class for the authentication app.
    
    Attributes:
        default_auto_field: Default primary key field type
        name: App name for Django registration
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_app'
    verbose_name = 'Authentication and User Management'
