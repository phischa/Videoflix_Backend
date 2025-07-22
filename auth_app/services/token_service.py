"""
Token Service for Account Activation
Uses Django's built-in token generator for secure tokens
"""
import logging
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from datetime import datetime, timedelta
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def _decode_uid(uidb64: str) -> Optional[User]:
    """Shared utility for decoding UIDs"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        return user
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        logger.warning(f"Error decoding UID {uidb64}: {e}")
        return None


class ActivationTokenService:
    """
    Service for account activation tokens
    
    Functions:
    - Generate tokens
    - Validate tokens  
    - Encode/decode UIDs
    - Check token expiration
    """
    
    @staticmethod
    def generate_activation_token(user: User) -> Tuple[str, str]:
        """
        Generates activation token for a user
        
        Args:
            user: Django User Model Instance
            
        Returns:
            Tuple[str, str]: (uidb64, token)
            - uidb64: Base64-encoded User-ID
            - token: Secure activation token
        """
        try:
            # Encode user ID to Base64
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Generate secure token
            token = default_token_generator.make_token(user)
            
            logger.info(f"Activation token generated for user {user.id} ({user.email})")
            
            return uidb64, token
            
        except Exception as e:
            logger.error(f"Error generating activation token for user {user.id}: {e}")
            raise
    
    @staticmethod
    def verify_activation_token(uidb64: str, token: str) -> Optional[User]:
        """
        Verifies an activation token
        
        Args:
            uidb64: Base64-encoded User-ID
            token: Activation token
            
        Returns:
            Optional[User]: User object if token valid, None if invalid
        """
        try:
            # Decode UID
            user = _decode_uid(uidb64)
            if not user:
                return None
            
            # Validate token
            if not default_token_generator.check_token(user, token):
                logger.warning(f"Invalid activation token for user {user.id} ({user.email})")
                return None
            
            # Check if user is already activated
            if user.is_active:
                logger.info(f"User {user.id} ({user.email}) already activated")
                return user  # Already activated, but still return as valid
            
            logger.info(f"Valid activation token for user {user.id} ({user.email})")
            return user
            
        except Exception as e:
            logger.error(f"Error verifying activation token: {e}")
            return None
    
    @staticmethod
    def activate_user(user: User) -> bool:
        """
        Activates a user account
        
        Args:
            user: User object to be activated
            
        Returns:
            bool: True if successfully activated, False on error
        """
        try:
            if user.is_active:
                logger.info(f"User {user.id} ({user.email}) already active")
                return True
            
            user.is_active = True
            user.save(update_fields=['is_active'])
            
            logger.info(f"User {user.id} ({user.email}) successfully activated")
            return True
            
        except Exception as e:
            logger.error(f"Error activating user {user.id}: {e}")
            return False
    
    @staticmethod
    def create_activation_url(uidb64: str, token: str, request=None) -> str:
        """
        Creates complete activation URL
        
        Args:
            uidb64: Base64-encoded User-ID
            token: Activation token
            request: Django Request Object (optional)
            
        Returns:
            str: Complete activation URL
        """
        # Frontend URL from settings
        backend_url = getattr(settings, 'BACKEND_URL', 'http://127.0.0.1:8000')
        
        # Activation path
        activation_path = f"/activate/{uidb64}/{token}/"
        
        # Complete URL
        if backend_url.endswith('/'):
            backend_url = backend_url.rstrip('/')
        
        activation_url = f"{backend_url}/api{activation_path}"
        
        logger.info(f"Created activation URL: {activation_url}")
        return activation_url
    
    @staticmethod
    def is_token_expired(user: User, max_age_hours: int = None) -> bool:
        """
        Checks if a token period has expired (additional security)
        
        Args:
            user: User object
            max_age_hours: Maximum age in hours (default from settings)
            
        Returns:
            bool: True if expired, False if still valid
        """
        if max_age_hours is None:
            max_age_hours = getattr(settings, 'ACTIVATION_TOKEN_EXPIRY_HOURS', 24)
        
        # User creation time + max_age
        expiry_time = user.date_joined + timedelta(hours=max_age_hours)
        
        is_expired = datetime.now(user.date_joined.tzinfo) > expiry_time
        
        if is_expired:
            logger.warning(f"Activation token expired for user {user.id} ({user.email})")
        
        return is_expired

class PasswordResetTokenService:
    """
    Service for password reset tokens
    
    Functions:
    - Generate tokens
    - Validate tokens  
    - Encode/decode UIDs
    - Check token expiration
    """
    
    @staticmethod
    def generate_password_reset_token(user: User) -> Tuple[str, str]:
        """
        Generates activation token for a user
        
        Args:
            user: Django User Model Instance
            
        Returns:
            Tuple[str, str]: (uidb64, token)
            - uidb64: Base64-encoded User-ID
            - token: Secure password reset token
        """
        try:
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            logger.info(f"Password reset token generated for user {user.id} ({user.email})")

            return uidb64, token
        except Exception as e:
            logger.error(f"Error generating password reset token for user {user.id}: {e}")
            raise
    
    @staticmethod
    def verify_password_reset_token(uidb64: str, token: str) -> Optional[User]:
        """
        Verifies an password reset token
        
        Args:
            uidb64: Base64-encoded User-ID
            token: Password reset token
            
        Returns:
            Optional[User]: User object if token valid, None if invalid
        """
        try:
            # Decode UID
            user = _decode_uid(uidb64)
            if not user:
                return None
            if not default_token_generator.check_token(user, token):
                logger.warning(f"Invalid activation token for user {user.id} ({user.email})")
                return None
            logger.info(f"Valid password reset token for user {user.id} ({user.email})")
            return user
            
        except Exception as e:
            logger.error(f"Error verifying activation token: {e}")
            return None
        
    @staticmethod
    def create_password_confirm_url(uidb64: str, token: str, request=None) -> str:
        """
        Creates complete password confirm URL
        
        Args:
            uidb64: Base64-encoded User-ID
            token: Password reset token
            request: Django Request Object (optional)
            
        Returns:
            str: Complete password confirm URL
        """
        # Backend URL from settings
        backend_url = getattr(settings, 'BACKEND_URL', 'http://127.0.0.1:8000')
        
        # Password confirm path
        password_confirm_path = f"/password_confirm/{uidb64}/{token}/"
        
        # Complete URL
        if backend_url.endswith('/'):
            backend_url = backend_url.rstrip('/')
        
        password_confirm_url = f"{backend_url}/api{password_confirm_path}"
        
        logger.info(f"Created password reset URL: {password_confirm_url}")
        return password_confirm_url
    
    @staticmethod
    def reset_user_password(user: User, new_password: str) -> bool:
        """
        Resets user password
        
        Args:
            user: User object
            new_password: New password to set
            
        Returns:
            bool: True if successfully reset, False on error
        """
        try:
            user.set_password(new_password)
            user.save(update_fields=['password'])
            
            logger.info(f"Password successfully reset for user {user.id} ({user.email})")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting password for user {user.id}: {e}")
            return False

# Convenience functions for direct import
def generate_activation_token(user: User) -> Tuple[str, str]:
    """Shortcut for token generation"""
    return ActivationTokenService.generate_activation_token(user)


def verify_activation_token(uidb64: str, token: str) -> Optional[User]:
    """Shortcut for token verification"""
    return ActivationTokenService.verify_activation_token(uidb64, token)


def activate_user(user: User) -> bool:
    """Shortcut for user activation"""
    return ActivationTokenService.activate_user(user)


def create_activation_url(uidb64: str, token: str, request=None) -> str:
    """Shortcut for URL generation"""
    return ActivationTokenService.create_activation_url(uidb64, token, request)


def generate_password_reset_token(user: User) -> Tuple[str, str]:
    """Shortcut for password reset token generation"""
    return PasswordResetTokenService.generate_password_reset_token(user)


def verify_password_reset_token(uidb64: str, token: str) -> Optional[User]:
    """Shortcut for password reset token verification"""
    return PasswordResetTokenService.verify_password_reset_token(uidb64, token)


def create_password_confirm_url(uidb64: str, token: str, request=None) -> str:
    """Shortcut for password confirm URL generation"""
    return PasswordResetTokenService.create_password_confirm_url(uidb64, token, request)


def reset_user_password(user: User, new_password: str) -> bool:
    """Shortcut for password reset"""
    return PasswordResetTokenService.reset_user_password(user, new_password)