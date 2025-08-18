import pytest
from django.core import mail
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.conf import settings
from unittest.mock import patch, Mock, MagicMock
from django.core.mail import send_mail
from django.template.loader import render_to_string

from auth_app.services import (
    send_activation_email,
    send_password_reset_email,
)


class TestSendActivationEmail:
    """Tests for send_activation_email function."""
    
    def setup_method(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
    def test_send_activation_email_success(self, user):
        """Test successful activation email sending."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        with patch('auth_app.services.generate_activation_token') as mock_generate_token, \
             patch('django.core.mail.send_mail') as mock_send_mail:
            
            mock_generate_token.return_value = ('test-uid64', 'test-token-123')
            mock_send_mail.return_value = True
            
            result = send_activation_email(user, request)
            
            assert result is True
            mock_generate_token.assert_called_once_with(user)
            mock_send_mail.assert_called_once()
            
            # Check email parameters
            call_args = mock_send_mail.call_args
            assert 'Account Activation' in call_args[0][0]  # Subject
            assert user.email in call_args[1]['recipient_list']
            
    def test_send_activation_email_token_generation_failure(self, user):
        """Test activation email when token generation fails."""
        request = self.factory.get('/')
        
        with patch('auth_app.services.generate_activation_token') as mock_generate_token:
            mock_generate_token.return_value = (None, None)
            
            result = send_activation_email(user, request)
            
            assert result is False
            
    def test_send_activation_email_mail_send_failure(self, user):
        """Test activation email when mail sending fails."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        with patch('auth_app.services.generate_activation_token') as mock_generate, \
             patch('django.core.mail.send_mail') as mock_send_mail:
            
            mock_generate.return_value = ('test-uid64', 'test-token-123')
            mock_send_mail.side_effect = Exception("SMTP Error")
            
            result = send_activation_email(user, request)
            
            assert result is False
            
    def test_send_activation_email_builds_correct_url(self, user):
        """Test that activation email builds correct activation URL."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        request.is_secure = lambda: False
        
        with patch('auth_app.services.generate_activation_token') as mock_generate, \
             patch('django.core.mail.send_mail') as mock_send_mail:
            
            mock_generate.return_value = ('test-uid64', 'test-token-123')
            mock_send_mail.return_value = True
            
            result = send_activation_email(user, request)
            
            assert result is True
            
            # Check that email content contains expected URL components
            call_args = mock_send_mail.call_args
            email_body = call_args[0][1]  # Message body
            assert 'test-uid64' in email_body
            assert 'test-token-123' in email_body
            assert 'activate' in email_body
            
    def test_send_activation_email_uses_correct_template(self, user):
        """Test that activation email uses correct template."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        with patch('auth_app.services.email_service.generate_activation_token') as mock_generate, \
             patch('django.template.loader.render_to_string') as mock_render, \
             patch('django.core.mail.send_mail') as mock_send_mail:
            
            mock_generate.return_value = ('test-uid64', 'test-token-123')
            mock_render.return_value = 'Rendered email content'
            mock_send_mail.return_value = True
            
            result = send_activation_email(user, request)
            
            assert result is True
            mock_render.assert_called_once()
            
            # Check template name and context
            call_args = mock_render.call_args
            template_name = call_args[0][0]
            context = call_args[0][1]
            
            assert 'activation' in template_name.lower()
            assert 'user' in context
            assert 'activation_url' in context
            
    def test_send_activation_email_with_https_request(self, user):
        """Test activation email with HTTPS request."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        request.is_secure = lambda: True
        
        with patch('auth_app.services.email_service.generate_activation_token') as mock_generate, \
             patch('django.core.mail.send_mail') as mock_send_mail:
            
            mock_generate.return_value = ('test-uid64', 'test-token-123')
            mock_send_mail.return_value = True
            
            result = send_activation_email(user, request)
            
            assert result is True
            
            # Check that HTTPS URL is used
            call_args = mock_send_mail.call_args
            email_body = call_args[0][1]
            assert 'https://' in email_body
            
    def test_send_activation_email_respects_email_settings(self, user):
        """Test that activation email respects Django email settings."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        with patch('auth_app.services.email_service.generate_activation_token') as mock_generate, \
             patch('django.core.mail.send_mail') as mock_send_mail:
            
            mock_generate.return_value = ('test-uid64', 'test-token-123')
            mock_send_mail.return_value = True
            
            result = send_activation_email(user, request)
            
            assert result is True
            
            # Check email sender
            call_args = mock_send_mail.call_args
            from_email = call_args[1]['from_email']
            assert from_email == settings.DEFAULT_FROM_EMAIL


class TestSendPasswordResetEmail:
    """Tests for send_password_reset_email function."""
    
    def setup_method(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
    def test_send_password_reset_email_success(self, user):
        """Test successful password reset email sending."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        with patch('auth_app.services.generate_password_reset_token') as mock_generate, \
             patch('django.core.mail.send_mail') as mock_send_mail:
            
            mock_generate.return_value = ('reset-uid64', 'reset-token-456')
            mock_send_mail.return_value = True
            
            result = send_password_reset_email(user, request)
            
            assert result is True
            mock_generate.assert_called_once_with(user)
            mock_send_mail.assert_called_once()
            
            # Check email parameters
            call_args = mock_send_mail.call_args
            assert 'Password Reset' in call_args[0][0]  # Subject
            assert user.email in call_args[1]['recipient_list']
            
    def test_send_password_reset_email_token_failure(self, user):
        """Test password reset email when token generation fails."""
        request = self.factory.get('/')
        
        with patch('auth_app.services.generate_password_reset_token') as mock_generate:
            mock_generate.return_value = (None, None)
            
            result = send_password_reset_email(user, request)
            
            assert result is False
            
    def test_send_password_reset_email_send_failure(self, user):
        """Test password reset email when sending fails."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        with patch('auth_app.services.generate_password_reset_token') as mock_generate, \
             patch('django.core.mail.send_mail') as mock_send_mail:
            
            mock_generate.return_value = ('reset-uid64', 'reset-token-456')
            mock_send_mail.side_effect = Exception("Mail server error")
            
            result = send_password_reset_email(user, request)
            
            assert result is False
            
    def test_send_password_reset_email_builds_correct_url(self, user):
        """Test that password reset email builds correct reset URL."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        request.is_secure = lambda: False
        
        with patch('auth_app.services.generate_password_reset_token') as mock_generate, \
             patch('django.core.mail.send_mail') as mock_send_mail:
            
            mock_generate.return_value = ('reset-uid64', 'reset-token-456')
            mock_send_mail.return_value = True
            
            result = send_password_reset_email(user, request)
            
            assert result is True
            
            # Check URL components in email
            call_args = mock_send_mail.call_args
            email_body = call_args[0][1]
            assert 'reset-uid64' in email_body
            assert 'reset-token-456' in email_body
            assert 'password_confirm' in email_body
            
    def test_send_password_reset_email_uses_template(self, user):
        """Test that password reset email uses correct template."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        with patch('auth_app.services.generate_password_reset_token') as mock_generate, \
             patch('django.template.loader.render_to_string') as mock_render, \
             patch('django.core.mail.send_mail') as mock_send_mail:
            
            mock_generate.return_value = ('reset-uid64', 'reset-token-456')
            mock_render.return_value = 'Password reset email content'
            mock_send_mail.return_value = True
            
            result = send_password_reset_email(user, request)
            
            assert result is True
            mock_render.assert_called_once()
            
            # Check template and context
            call_args = mock_render.call_args
            template_name = call_args[0][0]
            context = call_args[0][1]
            
            assert 'reset' in template_name.lower() or 'password' in template_name.lower()
            assert 'user' in context
            assert 'reset_url' in context
            
    def test_send_password_reset_email_security_considerations(self, user):
        """Test security aspects of password reset email."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        with patch('auth_app.services.email_service.generate_password_reset_token') as mock_generate, \
             patch('django.core.mail.send_mail') as mock_send_mail:
            
            mock_generate.return_value = ('reset-uid64', 'reset-token-456')
            mock_send_mail.return_value = True
            
            result = send_password_reset_email(user, request)
            
            assert result is True
            
            # Check that email doesn't contain sensitive information
            call_args = mock_send_mail.call_args
            email_body = call_args[0][1]
            
            # Should not contain password or other sensitive data
            assert user.password not in email_body
            assert 'password' not in email_body.lower() or 'reset' in email_body.lower()


class TestEmailServiceIntegration:
    """Integration tests for email services."""
    
    def setup_method(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
    def test_email_service_with_development_backend(self, user):
        """Test email service with console backend in development."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        # Test with DEBUG=True (console backend)
        with patch('django.conf.settings.DEBUG', True), \
             patch('auth_app.services.email_service.generate_activation_token') as mock_generate:
            
            mock_generate.return_value = ('test-uid64', 'test-token-123')
            
            # Should work with console backend
            result = send_activation_email(user, request)
            
            # Result depends on implementation, but should not crash
            assert isinstance(result, bool)
            
    def test_email_service_queue_integration(self, user):
        """Test email service integration with task queue (if used)."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        with patch('auth_app.services.generate_activation_token') as mock_generate:
            mock_generate.return_value = ('test-uid64', 'test-token-123')
            
            # Test that email functions can be called from queue context
            try:
                result = send_activation_email(user, request)
                assert isinstance(result, bool)
            except Exception as e:
                pytest.fail(f"Email service should work in queue context: {e}")
                
    def test_email_template_rendering_edge_cases(self, user):
        """Test email template rendering with edge cases."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        # Test with user having special characters in email
        user.email = 'test+special@example.com'
        user.save()
        
        with patch('auth_app.services.email_service.generate_activation_token') as mock_generate, \
             patch('django.core.mail.send_mail') as mock_send_mail:
            
            mock_generate.return_value = ('test-uid64', 'test-token-123')
            mock_send_mail.return_value = True
            
            result = send_activation_email(user, request)
            
            assert result is True
            
    def test_email_error_handling_robustness(self, user):
        """Test email service error handling robustness."""
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        
        # Test various error scenarios
        error_scenarios = [
            Exception("Network error"),
            ConnectionError("SMTP connection failed"),
            TimeoutError("Mail server timeout"),
        ]
        
        for error in error_scenarios:
            with patch('auth_app.services.email_service.generate_activation_token') as mock_generate, \
                 patch('django.core.mail.send_mail') as mock_send_mail:
                
                mock_generate.return_value = ('test-uid64', 'test-token-123')
                mock_send_mail.side_effect = error
                
                result = send_activation_email(user, request)
                
                # Should handle errors gracefully
                assert result is False
