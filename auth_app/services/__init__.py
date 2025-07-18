# auth_app/services/__init__.py
"""
Authentication Services Package

This package contains all services related to user authentication,
account activation, and user management.
"""

# Import all functions and classes from token_service and email_service
# We need to import them individually to avoid circular imports

try:
    # Token Service imports
    from .token_service import (
        ActivationTokenService,
        PasswordResetTokenService,
        generate_activation_token,
        verify_activation_token,
        activate_user,
        create_activation_url,
        generate_password_reset_token,
        verify_password_reset_token,
        create_password_confirm_url,
        reset_user_password,
    )
except ImportError as e:
    print(f"Error importing token_service: {e}")
    raise

try:
    # Email Service imports
    from .email_service import (
        ActivationEmailService,
        PasswordResetEmailService,
        send_activation_email,
        resend_activation_email,
        queue_activation_email,
        is_email_valid_format,
        get_email_stats,
        send_password_reset_email,
    )
except ImportError as e:
    print(f"Error importing email_service: {e}")
    raise

# Convenience exports for easy importing
__all__ = [
    # Token Service
    'ActivationTokenService',
    'PasswordResetTokenService',
    'generate_activation_token',
    'verify_activation_token', 
    'activate_user',
    'create_activation_url',
    'generate_password_reset_token',
    'verify_password_reset_token',
    'create_password_confirm_url',
    'reset_user_password',
    
    # Email Service
    'ActivationEmailService',
    'PasswordResetEmailService',
    'send_activation_email',
    'resend_activation_email',
    'queue_activation_email',
    'is_email_valid_format',
    'get_email_stats',
    'send_password_reset_email',
]