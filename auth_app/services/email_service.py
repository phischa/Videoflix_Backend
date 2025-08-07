"""
Enhanced Email Service for Account Activation and Password Reset
Handles sending emails with HTML and text templates, includes retry logic and configuration management
"""
import logging
import time
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpRequest
from django.core.exceptions import ImproperlyConfigured

# Import all token functions at the top (Fix A: Import-Probleme)
from .token_service import (
    generate_activation_token, 
    create_activation_url,
    generate_password_reset_token, 
    create_password_confirm_url
)

logger = logging.getLogger('email_service')


# Fix C: Zentrale Configuration-Klasse
@dataclass
class EmailConfig:
    """Zentrale Konfiguration für E-Mail-Services"""
    subject_prefix: str
    from_email: str
    support_email: str
    company_name: str
    site_name: str
    current_year: int
    activation_expiry_hours: int
    password_reset_expiry_hours: int
    use_async: bool
    async_queue: str
    timeout: int
    max_retries: int
    retry_delay: float
    
    @classmethod
    def from_settings(cls) -> 'EmailConfig':
        """Erstellt EmailConfig aus Django Settings"""
        return cls(
            subject_prefix=getattr(settings, 'EMAIL_SUBJECT_PREFIX', '[Videoflix] '),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@videoflix.com'),
            support_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@videoflix.com'),
            company_name='Videoflix',
            site_name='Videoflix',
            current_year=2025,
            activation_expiry_hours=getattr(settings, 'ACTIVATION_TOKEN_EXPIRY_HOURS', 24),
            password_reset_expiry_hours=getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRY_HOURS', 24),
            use_async=getattr(settings, 'USE_ASYNC_EMAILS', False),
            async_queue=getattr(settings, 'ASYNC_EMAIL_QUEUE', 'emails'),
            timeout=getattr(settings, 'EMAIL_TIMEOUT', 30),
            max_retries=getattr(settings, 'EMAIL_MAX_RETRIES', 3),
            retry_delay=getattr(settings, 'EMAIL_RETRY_DELAY', 1.0),
        )


# Fix B: Error Handling Classes
class EmailServiceError(Exception):
    """Base exception for email service errors"""
    pass


class EmailTemplateError(EmailServiceError):
    """Exception for template-related errors"""
    pass


class EmailSendError(EmailServiceError):
    """Exception for email sending errors"""
    pass


class EmailRetryableError(EmailSendError):
    """Exception for errors that should trigger retry"""
    pass


# Fix B: Retry Logic Implementation
class RetryManager:
    """Manages retry logic for email sending"""
    
    @staticmethod
    def with_retry(func, max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
        """
        Decorator-like function for retry logic with exponential backoff
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            delay: Initial delay between retries
            backoff_factor: Multiplier for delay on each retry
        """
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    return func(*args, **kwargs)
                except EmailRetryableError as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Email send attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"Email send failed after {max_retries + 1} attempts")
                except EmailServiceError as e:
                    # Non-retryable errors
                    logger.error(f"Non-retryable email error: {e}")
                    raise
                except Exception as e:
                    # Unexpected errors
                    logger.error(f"Unexpected error in email service: {e}")
                    raise EmailServiceError(f"Unexpected error: {e}")
            
            # If we get here, all retries failed
            raise EmailSendError(f"Failed after {max_retries + 1} attempts. Last error: {last_exception}")
        
        return wrapper


# Fix A: Bessere Code-Struktur - Base Class
class BaseEmailService:
    """Base class for all email services with improved structure"""
    
    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig.from_settings()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def _get_base_context(self) -> Dict[str, Any]:
        """Get base template context used by all emails"""
        return {
            'site_name': self.config.site_name,
            'company_name': self.config.company_name,
            'support_email': self.config.support_email,
            'current_year': self.config.current_year,
        }
    
    def _validate_template_exists(self, template_path: str) -> bool:
        """Check if template exists"""
        try:
            render_to_string(template_path, {})
            return True
        except TemplateDoesNotExist:
            return False
        except Exception:
            # Template exists but has other issues
            return True
    
    def _render_template_safe(self, template_path: str, context: Dict[str, Any], 
                             fallback_content: str = None) -> str:
        """
        Safely render template with fallback
        
        Args:
            template_path: Path to template
            context: Template context
            fallback_content: Fallback content if template fails
            
        Returns:
            str: Rendered content
            
        Raises:
            EmailTemplateError: If template rendering fails and no fallback
        """
        try:
            return render_to_string(template_path, context)
        except TemplateDoesNotExist:
            self.logger.error(f"Template not found: {template_path}")
            if fallback_content:
                self.logger.warning(f"Using fallback content for {template_path}")
                return fallback_content
            raise EmailTemplateError(f"Template not found: {template_path}")
        except Exception as e:
            self.logger.error(f"Template rendering error for {template_path}: {e}")
            if fallback_content:
                self.logger.warning(f"Using fallback content due to rendering error")
                return fallback_content
            raise EmailTemplateError(f"Template rendering failed: {e}")
    
    def _send_email_core(self, recipient_email: str, subject: str, 
                        text_content: str, html_content: str) -> bool:
        """
        Core email sending function with error handling
        
        Args:
            recipient_email: Email address to send to
            subject: Email subject line
            text_content: Plain text content
            html_content: HTML content
            
        Returns:
            bool: True if sent successfully
            
        Raises:
            EmailRetryableError: For retryable errors
            EmailSendError: For non-retryable errors
        """
        try:
            # Add subject prefix
            full_subject = f"{self.config.subject_prefix}{subject}"
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=full_subject,
                body=text_content,
                from_email=self.config.from_email,
                to=[recipient_email]
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Send email with timeout
            start_time = time.time()
            email.send()
            duration = time.time() - start_time
            
            self.logger.info(
                f"Email sent successfully to {recipient_email} "
                f"(duration: {duration:.2f}s, subject: {subject})"
            )
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Classify errors for retry logic
            retryable_errors = [
                'connection refused', 'timeout', 'temporary failure',
                'server too busy', 'rate limit', 'try again'
            ]
            
            if any(err in error_msg for err in retryable_errors):
                raise EmailRetryableError(f"Retryable SMTP error: {e}")
            else:
                raise EmailSendError(f"Non-retryable SMTP error: {e}")


# Fix A+B+C: Improved ActivationEmailService
class ActivationEmailService(BaseEmailService):
    """
    Service for sending account activation emails with improved error handling
    """
    
    # Template fallbacks
    TEXT_FALLBACK = """
Hallo {email}!

Vielen Dank für Ihre Registrierung bei {company_name}!

Um Ihr Konto zu aktivieren, besuchen Sie bitte den folgenden Link:
{activation_url}

Dieser Link ist {expiry_hours} Stunden gültig.

Mit freundlichen Grüßen,
Das {company_name} Team
"""
    
    HTML_FALLBACK = """
<!DOCTYPE html>
<html>
<head><title>Account aktivieren</title></head>
<body>
<h1>Willkommen bei {company_name}!</h1>
<p>Hallo {email}!</p>
<p>Um Ihr Konto zu aktivieren, klicken Sie bitte auf den folgenden Link:</p>
<p><a href="{activation_url}">Account aktivieren</a></p>
<p>Dieser Link ist {expiry_hours} Stunden gültig.</p>
<p>Mit freundlichen Grüßen,<br>Das {company_name} Team</p>
</body>
</html>
"""
    
    def send_activation_email(self, user: User, request: Optional[HttpRequest] = None) -> bool:
        """
        Sends activation email to a user with retry logic
        
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
            context = self._get_activation_context(user, activation_url)
            
            # Use retry logic for sending
            send_func = RetryManager.with_retry(
                self._send_activation_email_core,
                max_retries=self.config.max_retries,
                delay=self.config.retry_delay
            )
            
            success = send_func(user.email, context)
            
            if success:
                self.logger.info(f"Activation email sent successfully to {user.email} (User ID: {user.id})")
                return token
            
        except Exception as e:
            self.logger.error(f"Error sending activation email to {user.email}: {e}")
        
        return None
    
    def _get_activation_context(self, user: User, activation_url: str) -> Dict[str, Any]:
        """
        Prepares template context for activation email
        """
        context = self._get_base_context()
        context.update({
            'user': user,
            'activation_url': activation_url,
            'expiry_hours': self.config.activation_expiry_hours,
            'email': user.email,  # For fallback templates
        })
        return context
    
    def _send_activation_email_core(self, recipient_email: str, context: Dict[str, Any]) -> bool:
        """
        Core function for sending activation email with template fallbacks
        """
        # Prepare fallback content
        text_fallback = self.TEXT_FALLBACK.format(**context)
        html_fallback = self.HTML_FALLBACK.format(**context)
        
        # Render templates with fallbacks
        text_content = self._render_template_safe(
            'emails/activation_email.txt', 
            context, 
            text_fallback
        )
        html_content = self._render_template_safe(
            'emails/activation_email.html', 
            context, 
            html_fallback
        )
        
        # Send email
        return self._send_email_core(
            recipient_email=recipient_email,
            subject="Account aktivieren",
            text_content=text_content,
            html_content=html_content
        )
    
    def resend_activation_email(self, user: User, request: Optional[HttpRequest] = None) -> bool:
        """
        Resends activation email for a user (if not already activated)
        """
        if user.is_active:
            self.logger.info(f"User {user.email} is already activated, skipping email")
            return False
        
        return self.send_activation_email(user, request)


# Fix A+B+C: Improved PasswordResetEmailService
class PasswordResetEmailService(BaseEmailService):
    """
    Service for sending password reset emails with improved error handling
    """
    
    # Template fallbacks
    TEXT_FALLBACK = """
Hallo {email}!

Sie haben eine Anfrage zum Zurücksetzen Ihres Passworts gestellt.

Um ein neues Passwort zu erstellen, kopieren Sie den folgenden Link:
{reset_url}

Dieser Link ist {expiry_hours} Stunden gültig.

Falls Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail.

Mit freundlichen Grüßen,
Das {company_name} Sicherheitsteam
"""
    
    HTML_FALLBACK = """
<!DOCTYPE html>
<html>
<head><title>Passwort zurücksetzen</title></head>
<body>
<h1>Passwort zurücksetzen</h1>
<p>Hallo {email}!</p>
<p>Sie haben eine Anfrage zum Zurücksetzen Ihres Passworts gestellt.</p>
<p><a href="{reset_url}">Neues Passwort erstellen</a></p>
<p>Dieser Link ist {expiry_hours} Stunden gültig.</p>
<p>Falls Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail.</p>
<p>Mit freundlichen Grüßen,<br>Das {company_name} Sicherheitsteam</p>
</body>
</html>
"""
    
    def send_password_reset_email(self, user: User, request: Optional[HttpRequest] = None) -> bool:
        """
        Sends password reset email to a user with retry logic
        """
        try:
            # Generate password reset token
            uidb64, token = generate_password_reset_token(user)
            
            # Create password reset URL
            reset_url = create_password_confirm_url(uidb64, token, request)
            
            # Prepare email context
            context = self._get_password_reset_context(user, reset_url)
            
            # Use retry logic for sending
            send_func = RetryManager.with_retry(
                self._send_password_reset_email_core,
                max_retries=self.config.max_retries,
                delay=self.config.retry_delay
            )
            
            success = send_func(user.email, context)
            
            if success:
                self.logger.info(f"Password reset email sent successfully to {user.email} (User ID: {user.id})")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending password reset email to {user.email}: {e}")
            return False
    
    def _get_password_reset_context(self, user: User, reset_url: str) -> Dict[str, Any]:
        """
        Prepares template context for password reset email
        """
        context = self._get_base_context()
        context.update({
            'user': user,
            'reset_url': reset_url,
            'expiry_hours': self.config.password_reset_expiry_hours,
            'email': user.email,  # For fallback templates
        })
        return context
    
    def _send_password_reset_email_core(self, recipient_email: str, context: Dict[str, Any]) -> bool:
        """
        Core function for sending password reset email with template fallbacks
        """
        # Prepare fallback content
        text_fallback = self.TEXT_FALLBACK.format(**context)
        html_fallback = self.HTML_FALLBACK.format(**context)
        
        # Render templates with fallbacks
        text_content = self._render_template_safe(
            'emails/password_reset_email.txt', 
            context, 
            text_fallback
        )
        html_content = self._render_template_safe(
            'emails/password_reset_email.html', 
            context, 
            html_fallback
        )
        
        # Send email
        return self._send_email_core(
            recipient_email=recipient_email,
            subject="Passwort zurücksetzen",
            text_content=text_content,
            html_content=html_content
        )


# Fix A: Verbesserte Convenience Functions
def send_activation_email(user: User, request: Optional[HttpRequest] = None, 
                         config: Optional[EmailConfig] = None) -> bool:
    """
    Main function for sending activation emails
    
    Args:
        user: User object
        request: Django request object (optional)
        config: Custom email configuration (optional)
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    service = ActivationEmailService(config)
    return service.send_activation_email(user, request)


def send_password_reset_email(user: User, request: Optional[HttpRequest] = None,
                             config: Optional[EmailConfig] = None) -> bool:
    """
    Main function for sending password reset emails
    
    Args:
        user: User object
        request: Django request object (optional)
        config: Custom email configuration (optional)
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    service = PasswordResetEmailService(config)
    return service.send_password_reset_email(user, request)


def resend_activation_email(user: User, request: Optional[HttpRequest] = None) -> bool:
    """
    Convenience function for resending activation emails
    
    Args:
        user: User object
        request: Django request object (optional)
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    service = ActivationEmailService()
    return service.resend_activation_email(user, request)


# Fix A+C: Email Service Factory
class EmailServiceFactory:
    """Factory for creating email services with consistent configuration"""
    
    _config = None
    
    @classmethod
    def get_config(cls) -> EmailConfig:
        """Get cached configuration"""
        if cls._config is None:
            cls._config = EmailConfig.from_settings()
        return cls._config
    
    @classmethod
    def create_activation_service(cls) -> ActivationEmailService:
        """Create activation email service"""
        return ActivationEmailService(cls.get_config())
    
    @classmethod
    def create_password_reset_service(cls) -> PasswordResetEmailService:
        """Create password reset email service"""
        return PasswordResetEmailService(cls.get_config())
    
    @classmethod
    def refresh_config(cls):
        """Refresh cached configuration (useful for tests)"""
        cls._config = None


# Fix B: Health Check Functions
def health_check_email() -> Dict[str, Any]:
    """
    Health check for email service
    
    Returns:
        Dict[str, Any]: Health status
    """
    try:
        from django.core.mail import get_connection
        
        config = EmailConfig.from_settings()
        
        # Test connection
        connection = get_connection()
        connection.open()
        connection.close()
        
        return {
            'status': 'healthy',
            'email_backend': settings.EMAIL_BACKEND,
            'connection': True,
            'config': {
                'from_email': config.from_email,
                'timeout': config.timeout,
                'max_retries': config.max_retries,
            }
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'connection': False,
            'error': str(e)
        }


# Fix C: Configuration Validation
def validate_email_config() -> Tuple[bool, list]:
    """
    Validate email configuration
    
    Returns:
        Tuple[bool, list]: (is_valid, error_messages)
    """
    errors = []
    
    try:
        config = EmailConfig.from_settings()
        
        # Check required settings
        if not config.from_email:
            errors.append("DEFAULT_FROM_EMAIL not configured")
        
        if not hasattr(settings, 'EMAIL_BACKEND'):
            errors.append("EMAIL_BACKEND not configured")
        
        # Check template existence
        templates_to_check = [
            'emails/activation_email.txt',
            'emails/activation_email.html',
            'emails/password_reset_email.txt',
            'emails/password_reset_email.html',
        ]
        
        for template in templates_to_check:
            try:
                render_to_string(template, {})
            except TemplateDoesNotExist:
                # Not an error, we have fallbacks
                pass
            except Exception as e:
                errors.append(f"Template {template} has errors: {e}")
        
        return len(errors) == 0, errors
        
    except Exception as e:
        errors.append(f"Configuration error: {e}")
        return False, errors


def test_email_service(send_test_email: bool = True, recipient: Optional[str] = None) -> Dict[str, Any]:
    """
    Comprehensive test function for email service
    
    Args:
        send_test_email: Whether to actually send a test email
        recipient: Email address to send test to (defaults to DEFAULT_FROM_EMAIL)
        
    Returns:
        Dict[str, Any]: Test results and information
    """
    results = {
        'timestamp': time.time(),
        'django_debug': settings.DEBUG,
        'tests': {},
        'summary': 'Unknown'
    }
    
    print("🧪 EMAIL SERVICE TEST")
    print("=" * 50)
    
    # Test 1: Configuration Check
    print("1️⃣ Testing configuration...")
    try:
        config = EmailConfig.from_settings()
        is_valid, errors = validate_email_config()
        
        results['tests']['configuration'] = {
            'status': 'PASS' if is_valid else 'FAIL',
            'errors': errors,
            'config': {
                'email_backend': settings.EMAIL_BACKEND,
                'from_email': config.from_email,
                'use_async': config.use_async,
                'max_retries': config.max_retries,
            }
        }
        
        if is_valid:
            print("   ✅ Configuration valid")
            print(f"   📧 From: {config.from_email}")
            print(f"   🔧 Backend: {settings.EMAIL_BACKEND}")
        else:
            print("   ❌ Configuration errors:")
            for error in errors:
                print(f"      - {error}")
                
    except Exception as e:
        results['tests']['configuration'] = {
            'status': 'ERROR',
            'error': str(e)
        }
        print(f"   ❌ Configuration test failed: {e}")
    
    # Test 2: SMTP Connection (only if not console backend)
    print("\n2️⃣ Testing SMTP connection...")
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        print("   ⚠️  Using console backend (development mode)")
        results['tests']['smtp_connection'] = {
            'status': 'SKIP',
            'reason': 'Console backend in use'
        }
    else:
        try:
            from django.core.mail import get_connection
            connection = get_connection()
            connection.open()
            connection.close()
            
            print("   ✅ SMTP connection successful")
            results['tests']['smtp_connection'] = {
                'status': 'PASS',
                'host': getattr(settings, 'EMAIL_HOST', 'Unknown'),
                'port': getattr(settings, 'EMAIL_PORT', 'Unknown'),
            }
            
        except Exception as e:
            print(f"   ❌ SMTP connection failed: {e}")
            results['tests']['smtp_connection'] = {
                'status': 'FAIL',
                'error': str(e)
            }
    
    # Test 3: Template Rendering
    print("\n3️⃣ Testing template rendering...")
    try:
        service = ActivationEmailService()
        
        # Create dummy context
        from django.contrib.auth.models import User
        dummy_user = User(email="test@example.com", id=999)
        context = service._get_base_context()
        context.update({
            'user': dummy_user,
            'activation_url': 'https://example.com/activate/test/token/',
            'expiry_hours': 24
        })
        
        # Try to render templates (with fallbacks)
        text_content = service._render_template_safe(
            'emails/activation_email.txt', 
            context,
            service.TEXT_FALLBACK.format(**context)
        )
        html_content = service._render_template_safe(
            'emails/activation_email.html',
            context, 
            service.HTML_FALLBACK.format(**context)
        )
        
        print("   ✅ Template rendering successful")
        print(f"   📝 Text length: {len(text_content)} chars")
        print(f"   🌐 HTML length: {len(html_content)} chars")
        
        results['tests']['template_rendering'] = {
            'status': 'PASS',
            'text_length': len(text_content),
            'html_length': len(html_content)
        }
        
    except Exception as e:
        print(f"   ❌ Template rendering failed: {e}")
        results['tests']['template_rendering'] = {
            'status': 'FAIL',
            'error': str(e)
        }
    
    # Test 4: Send Test Email (optional)
    if send_test_email:
        print("\n4️⃣ Sending test email...")
        
        if not recipient:
            recipient = config.from_email
        
        try:
            # Create test email
            from django.core.mail import EmailMultiAlternatives
            
            subject = f"[Videoflix Test] Email Service Test - {time.strftime('%Y-%m-%d %H:%M:%S')}"
            text_content = f"""
Videoflix Email Service Test

This is a test email to verify your email configuration.

Test Details:
- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
- Django DEBUG: {settings.DEBUG}
- Email Backend: {settings.EMAIL_BACKEND}
- From: {config.from_email}
- To: {recipient}

If you received this email, your email service is working correctly!

--
Videoflix Team
"""
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head><title>Videoflix Email Test</title></head>
<body>
<h2>🧪 Videoflix Email Service Test</h2>
<p>This is a test email to verify your email configuration.</p>

<h3>Test Details:</h3>
<ul>
<li><strong>Timestamp:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</li>
<li><strong>Django DEBUG:</strong> {settings.DEBUG}</li>
<li><strong>Email Backend:</strong> {settings.EMAIL_BACKEND}</li>
<li><strong>From:</strong> {config.from_email}</li>
<li><strong>To:</strong> {recipient}</li>
</ul>

<p>✅ <strong>If you received this email, your email service is working correctly!</strong></p>

<hr>
<p><em>Videoflix Team</em></p>
</body>
</html>
"""
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=config.from_email,
                to=[recipient]
            )
            email.attach_alternative(html_content, "text/html")
            
            start_time = time.time()
            email.send()
            duration = time.time() - start_time
            
            print(f"   ✅ Test email sent successfully!")
            print(f"   📧 To: {recipient}")
            print(f"   ⏱️  Duration: {duration:.2f}s")
            
            results['tests']['test_email'] = {
                'status': 'PASS',
                'recipient': recipient,
                'duration': duration,
                'subject': subject
            }
            
        except Exception as e:
            print(f"   ❌ Test email failed: {e}")
            results['tests']['test_email'] = {
                'status': 'FAIL',
                'error': str(e),
                'recipient': recipient
            }
    else:
        print("\n4️⃣ Skipping test email (send_test_email=False)")
        results['tests']['test_email'] = {
            'status': 'SKIP',
            'reason': 'Disabled by parameter'
        }
    
    # Summary
    print("\n" + "=" * 50)
    
    # Calculate overall status
    statuses = [test.get('status', 'UNKNOWN') for test in results['tests'].values()]
    if any(status == 'FAIL' for status in statuses):
        overall_status = 'SOME TESTS FAILED'
        print("❌ OVERALL RESULT: SOME TESTS FAILED")
    elif any(status == 'ERROR' for status in statuses):
        overall_status = 'ERRORS ENCOUNTERED'
        print("⚠️  OVERALL RESULT: ERRORS ENCOUNTERED")
    elif all(status in ['PASS', 'SKIP'] for status in statuses):
        overall_status = 'ALL TESTS PASSED'
        print("✅ OVERALL RESULT: ALL TESTS PASSED")
    else:
        overall_status = 'UNKNOWN STATUS'
        print("❓ OVERALL RESULT: UNKNOWN STATUS")
    
    results['summary'] = overall_status
    
    # Next steps
    if overall_status == 'ALL TESTS PASSED':
        print("\n🚀 NEXT STEPS:")
        print("   1. Your email service is ready!")
        print("   2. Test user registration/password reset")
        print("   3. Configure RQ workers for async emails")
    else:
        print("\n🔧 TROUBLESHOOTING:")
        if any(test.get('status') == 'FAIL' for test in results['tests'].values() if 'smtp' in str(test)):
            print("   - Check your SMTP settings in .env")
            print("   - Verify email host, port, username, password")
            print("   - Check if your email provider requires app passwords")
    
    return results
    