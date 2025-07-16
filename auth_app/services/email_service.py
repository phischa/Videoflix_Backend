"""
Email Service for Account Activation
Handles sending activation emails with HTML and text templates
"""
import logging
from typing import Optional, Dict, Any
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpRequest

from .token_service import generate_activation_token, create_activation_url

logger = logging.getLogger(__name__)


class ActivationEmailService:
    """
    Service for sending account activation emails
    
    Features:
    - HTML + Text email templates
    - Token generation and URL creation
    - Error handling and logging
    - Template context management
    """
    
    @staticmethod
    def send_activation_email(user: User, request: Optional[HttpRequest] = None) -> bool:
        """
        Sends activation email to a user
        
        Args:
            user: User object to send activation email to
            request: Django request object (optional, for URL building)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Generate activation token
            uidb64, token = generate_activation_token(user)
            
            # Create activation URL
            activation_url = create_activation_url(uidb64, token, request)
            
            # Prepare email context
            context = ActivationEmailService._get_email_context(user, activation_url)
            
            # Send email
            success = ActivationEmailService._send_email(user.email, context)
            
            if success:
                logger.info(f"Activation email sent successfully to {user.email} (User ID: {user.id})")
            else:
                logger.error(f"Failed to send activation email to {user.email} (User ID: {user.id})")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending activation email to {user.email}: {e}")
            return False
    
    @staticmethod
    def _get_email_context(user: User, activation_url: str) -> Dict[str, Any]:
        """
        Prepares template context for activation email
        
        Args:
            user: User object
            activation_url: Complete activation URL
            
        Returns:
            Dict[str, Any]: Template context dictionary
        """
        return {
            'user': user,
            'activation_url': activation_url,
            'site_name': 'Videoflix',
            'company_name': 'Videoflix',
            'support_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@videoflix.com'),
            'current_year': 2025,
            'expiry_hours': getattr(settings, 'ACTIVATION_TOKEN_EXPIRY_HOURS', 24),
        }
    
    @staticmethod
    def _send_email(recipient_email: str, context: Dict[str, Any]) -> bool:
        """
        Sends the actual email with HTML and text templates
        
        Args:
            recipient_email: Email address to send to
            context: Template context dictionary
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Email subject
            subject = f"{getattr(settings, 'EMAIL_SUBJECT_PREFIX', '[Videoflix] ')}Account aktivieren"
            
            # Render templates
            text_content = render_to_string('emails/activation_email.txt', context)
            html_content = render_to_string('emails/activation_email.html', context)
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL'),
                to=[recipient_email]
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {recipient_email}: {e}")
            return False
    
    @staticmethod
    def resend_activation_email(user: User, request: Optional[HttpRequest] = None) -> bool:
        """
        Resends activation email for a user (if not already activated)
        
        Args:
            user: User object
            request: Django request object (optional)
            
        Returns:
            bool: True if email sent, False if user already active or error
        """
        if user.is_active:
            logger.info(f"User {user.email} is already activated, skipping email")
            return False
        
        return ActivationEmailService.send_activation_email(user, request)


# ==========================================
# ASYNC EMAIL SERVICE (OPTIONAL WITH RQ)
# ==========================================

def send_activation_email_async(user_id: int, request_data: Optional[Dict] = None):
    """
    Async function for sending activation emails via RQ
    
    Args:
        user_id: ID of user to send email to
        request_data: Serialized request data (optional)
    """
    try:
        from django.contrib.auth.models import User
        
        user = User.objects.get(id=user_id)
        
        # Send email synchronously within the job
        success = ActivationEmailService.send_activation_email(user, request=None)
        
        if success:
            logger.info(f"Async activation email sent to {user.email}")
        else:
            logger.error(f"Async activation email failed for {user.email}")
            
        return success
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found for async email")
        return False
    except Exception as e:
        logger.error(f"Error in async email job for user {user_id}: {e}")
        return False


def queue_activation_email(user: User, request: Optional[HttpRequest] = None) -> bool:
    """
    Queues activation email for async sending via RQ
    
    Args:
        user: User object
        request: Django request object (optional)
        
    Returns:
        bool: True if queued successfully, False otherwise
    """
    try:
        import django_rq
        
        # Get RQ queue
        queue = django_rq.get_queue('emails')  # Uses 'emails' queue from settings
        
        # Serialize request data if needed
        request_data = None
        if request:
            request_data = {
                'META': dict(request.META),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        
        # Queue the job
        job = queue.enqueue(
            send_activation_email_async,
            user.id,
            request_data,
            timeout=300  # 5 minutes timeout
        )
        
        logger.info(f"Activation email queued for {user.email} (Job ID: {job.id})")
        return True
        
    except ImportError:
        logger.warning("django-rq not available, falling back to synchronous email")
        return ActivationEmailService.send_activation_email(user, request)
    except Exception as e:
        logger.error(f"Error queuing activation email for {user.email}: {e}")
        return False


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

def send_activation_email(user: User, request: Optional[HttpRequest] = None, async_send: bool = False) -> bool:
    """
    Main function for sending activation emails
    
    Args:
        user: User object
        request: Django request object (optional)
        async_send: Whether to send asynchronously via RQ (default: False)
        
    Returns:
        bool: True if sent/queued successfully, False otherwise
    """
    if async_send:
        return queue_activation_email(user, request)
    else:
        return ActivationEmailService.send_activation_email(user, request)


def resend_activation_email(user: User, request: Optional[HttpRequest] = None) -> bool:
    """
    Convenience function for resending activation emails
    
    Args:
        user: User object
        request: Django request object (optional)
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    return ActivationEmailService.resend_activation_email(user, request)


# ==========================================
# EMAIL VERIFICATION HELPERS
# ==========================================

def is_email_valid_format(email: str) -> bool:
    """
    Basic email format validation
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if format is valid, False otherwise
    """
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_email_stats() -> Dict[str, int]:
    """
    Gets email sending statistics (for monitoring)
    
    Returns:
        Dict[str, int]: Statistics dictionary
    """
    # This could be extended with actual database queries
    # For now, return basic info
    from django.contrib.auth.models import User
    
    return {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'inactive_users': User.objects.filter(is_active=False).count(),
    }