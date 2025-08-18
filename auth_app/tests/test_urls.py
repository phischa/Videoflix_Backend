import pytest
from django.urls import reverse, resolve
from django.test import RequestFactory
from django.http import Http404

from auth_app.api.views import (
    RegistrationView,
    LogoutView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    AccountActivationView,
    PasswordResetView,
    PasswordConfirmView,
    HelloWorldView,
)


class TestAuthAppUrls:
    """Tests for auth_app URL routing."""
    
    def setup_method(self):
        """Set up test."""
        self.factory = RequestFactory()
    
    def test_register_url_resolves(self):
        """Test register URL resolves to correct view."""
        url = reverse('register')
        assert url == '/api/register/'
        
        resolver = resolve(url)
        assert resolver.func.view_class == RegistrationView
        
    def test_login_url_resolves(self):
        """Test login URL resolves to correct view."""
        url = reverse('token_obtain_pair')
        assert url == '/api/login/'
        
        resolver = resolve(url)
        assert resolver.func.view_class == CookieTokenObtainPairView
        
    def test_logout_url_resolves(self):
        """Test logout URL resolves to correct view."""
        url = reverse('logout')
        assert url == '/api/logout/'
        
        resolver = resolve(url)
        assert resolver.func.view_class == LogoutView
        
    def test_token_refresh_url_resolves(self):
        """Test token refresh URL resolves to correct view."""
        url = reverse('token_refresh')
        assert url == '/api/token/refresh/'
        
        resolver = resolve(url)
        assert resolver.func.view_class == CookieTokenRefreshView
        
    def test_account_activation_url_resolves(self):
        """Test account activation URL resolves to correct view."""
        url = reverse('account_activate', kwargs={
            'uidb64': 'dGVzdA', 
            'token': 'test-token-123'
        })
        assert url == '/api/activate/dGVzdA/test-token-123/'
        
        resolver = resolve(url)
        assert resolver.func.view_class == AccountActivationView
        assert resolver.kwargs['uidb64'] == 'dGVzdA'
        assert resolver.kwargs['token'] == 'test-token-123'
        
    def test_password_reset_url_resolves(self):
        """Test password reset URL resolves to correct view."""
        url = reverse('password_reset')
        assert url == '/api/password_reset/'
        
        resolver = resolve(url)
        assert resolver.func.view_class == PasswordResetView
        
    def test_password_confirm_url_resolves(self):
        """Test password confirm URL resolves to correct view."""
        url = reverse('password_confirm', kwargs={
            'uidb64': 'dGVzdA',
            'token': 'test-token-123'
        })
        assert url == '/api/password_confirm/dGVzdA/test-token-123/'
        
        resolver = resolve(url)
        assert resolver.func.view_class == PasswordConfirmView
        assert resolver.kwargs['uidb64'] == 'dGVzdA'
        assert resolver.kwargs['token'] == 'test-token-123'
        
    def test_hello_world_url_resolves(self):
        """Test hello world URL resolves to correct view."""
        url = reverse('hello')
        assert url == '/api/hello/'
        
        resolver = resolve(url)
        assert resolver.func.view_class == HelloWorldView


class TestUrlParameters:
    """Tests for URL parameters and patterns."""
    
    def test_activation_url_with_complex_parameters(self):
        """Test activation URL with complex but valid parameters."""
        uidb64 = 'bXktdGVzdC11c2VyLWlkLWNvbXBsZXg'  # Complex base64
        token = 'abcd1234-efgh5678-ijkl9012'
        
        url = reverse('account_activate', kwargs={
            'uidb64': uidb64,
            'token': token
        })
        
        resolver = resolve(url)
        assert resolver.kwargs['uidb64'] == uidb64
        assert resolver.kwargs['token'] == token
        
    def test_password_confirm_url_with_complex_parameters(self):
        """Test password confirm URL with complex but valid parameters."""
        uidb64 = 'bXktdGVzdC11c2VyLWlkLWNvbXBsZXg'
        token = 'xyz789-abc123-def456'
        
        url = reverse('password_confirm', kwargs={
            'uidb64': uidb64,
            'token': token
        })
        
        resolver = resolve(url)
        assert resolver.kwargs['uidb64'] == uidb64
        assert resolver.kwargs['token'] == token
        
    def test_url_patterns_accept_alphanumeric_tokens(self):
        """Test URL patterns accept alphanumeric tokens with hyphens."""
        test_cases = [
            'simple123',
            'test-token-123',
            'abc123def456',
            '123-456-789',
            'very-long-token-name-123456789'
        ]
        
        for token in test_cases:
            url = reverse('account_activate', kwargs={
                'uidb64': 'dGVzdA',
                'token': token
            })
            
            resolver = resolve(url)
            assert resolver.kwargs['token'] == token
    
    def test_base64_uidb64_patterns(self):
        """Test various base64 patterns for uidb64."""
        test_cases = [
            'dGVzdA',  # Simple
            'bXktdGVzdC11c2VyLWlk',  # Complex
            'YWJjZGVmZ2hpams',  # Another pattern
            'MTIzNDU2Nzg5MA'  # Numbers encoded
        ]
        
        for uidb64 in test_cases:
            url = reverse('account_activate', kwargs={
                'uidb64': uidb64,
                'token': 'test-token'
            })
            
            resolver = resolve(url)
            assert resolver.kwargs['uidb64'] == uidb64


class TestUrlReverseAndResolve:
    """Tests for URL reverse and resolve functionality."""
    
    def test_all_urls_reverse_correctly(self):
        """Test that all URLs can be reversed without errors."""
        # Simple URLs without parameters
        simple_urls = [
            'register',
            'token_obtain_pair', 
            'logout',
            'token_refresh',
            'password_reset',
            'hello'
        ]
        
        for url_name in simple_urls:
            url = reverse(url_name)
            assert url is not None
            assert url.startswith('/')
            
    def test_parameterized_urls_reverse_correctly(self):
        """Test that parameterized URLs reverse correctly."""
        # URLs with parameters
        param_urls = [
            ('account_activate', {'uidb64': 'test123', 'token': 'token123'}),
            ('password_confirm', {'uidb64': 'test456', 'token': 'token456'})
        ]
        
        for url_name, kwargs in param_urls:
            url = reverse(url_name, kwargs=kwargs)
            assert url is not None
            assert url.startswith('/')
            
            # Test that URL resolves back correctly
            resolver = resolve(url)
            assert resolver.url_name == url_name
            for key, value in kwargs.items():
                assert resolver.kwargs[key] == value
                
    def test_url_namespace_handling(self):
        """Test URL namespace handling if any."""
        # Test that URLs resolve without namespace issues
        url = reverse('register')
        resolver = resolve(url)
        assert resolver.url_name == 'register'
        
    def test_invalid_url_parameters_raise_errors(self):
        """Test that invalid parameters raise appropriate errors."""
        with pytest.raises(Exception):  # Should raise some form of URL error
            reverse('account_activate', kwargs={'uidb64': 'test'})  # Missing token
            
        with pytest.raises(Exception):
            reverse('password_confirm', kwargs={'token': 'test'})  # Missing uidb64


class TestUrlSecurity:
    """Tests for URL security considerations."""
    
    def test_sensitive_urls_patterns(self):
        """Test that sensitive URLs have proper patterns."""
        # Account activation URL should accept secure patterns
        url = reverse('account_activate', kwargs={
            'uidb64': 'c2VjdXJlLXVzZXItaWQ',
            'token': 'secure-activation-token-12345'
        })
        
        resolver = resolve(url)
        assert resolver.kwargs['uidb64'] == 'c2VjdXJlLXVzZXItaWQ'
        assert resolver.kwargs['token'] == 'secure-activation-token-12345'
        
    def test_password_reset_url_patterns(self):
        """Test password reset URL patterns for security."""
        url = reverse('password_confirm', kwargs={
            'uidb64': 'cGFzc3dvcmQtcmVzZXQtdWlk',
            'token': 'password-reset-token-67890'
        })
        
        resolver = resolve(url)
        assert resolver.kwargs['uidb64'] == 'cGFzc3dvcmQtcmVzZXQtdWlk'
        assert resolver.kwargs['token'] == 'password-reset-token-67890'
        
    def test_url_case_sensitivity(self):
        """Test URL case sensitivity."""
        # URLs should be case sensitive for security
        url1 = reverse('account_activate', kwargs={
            'uidb64': 'TestCase',
            'token': 'token123'
        })
        
        url2 = reverse('account_activate', kwargs={
            'uidb64': 'testcase', 
            'token': 'token123'
        })
        
        # URLs should be different (case sensitive)
        assert url1 != url2
        