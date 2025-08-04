import pytest
from django.contrib.auth.models import User
from unittest.mock import Mock, patch
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from auth_app.authentication import CookieJWTAuthentication


class TestCookieJWTAuthentication:
    """Tests for CookieJWTAuthentication class."""
    
    def setup_method(self):
        """Set up test instance."""
        self.auth = CookieJWTAuthentication()
        
    def test_get_raw_token_from_header(self, mock_request, user, jwt_tokens):
        """Test token extraction from Authorization header."""
        mock_request.META['HTTP_AUTHORIZATION'] = f'Bearer {jwt_tokens["access"]}'
        mock_request.COOKIES = {}
        
        with patch('auth_app.authentication.logger') as mock_logger:
            token = self.auth.get_raw_token(mock_request)
            
            assert token == jwt_tokens["access"]
            mock_logger.error.assert_called()
            
    def test_get_raw_token_from_cookie(self, mock_request, user, jwt_tokens):
        """Test token extraction from cookie."""
        mock_request.META = {}
        mock_request.COOKIES = {'access_token': jwt_tokens["access"]}
        
        with patch('auth_app.authentication.logger') as mock_logger:
            token = self.auth.get_raw_token(mock_request)
            
            assert token == jwt_tokens["access"]
            mock_logger.error.assert_called()
            
    def test_get_raw_token_header_priority(self, mock_request, user, jwt_tokens):
        """Test that header token takes priority over cookie."""
        header_token = jwt_tokens["access"]
        cookie_token = "different_token"
        
        mock_request.META['HTTP_AUTHORIZATION'] = f'Bearer {header_token}'
        mock_request.COOKIES = {'access_token': cookie_token}
        
        with patch('auth_app.authentication.logger'):
            token = self.auth.get_raw_token(mock_request)
            
            assert token == header_token
            assert token != cookie_token
            
    def test_get_raw_token_invalid_header_format(self, mock_request, user, jwt_tokens):
        """Test token extraction with invalid header format."""
        mock_request.META['HTTP_AUTHORIZATION'] = 'InvalidFormat token'
        mock_request.COOKIES = {'access_token': jwt_tokens["access"]}
        
        with patch('auth_app.authentication.logger'):
            token = self.auth.get_raw_token(mock_request)
            
            # Should fall back to cookie
            assert token == jwt_tokens["access"]
            
    def test_get_raw_token_malformed_header(self, mock_request, user, jwt_tokens):
        """Test token extraction with malformed header."""
        mock_request.META['HTTP_AUTHORIZATION'] = 'Bearer'  # Missing token part
        mock_request.COOKIES = {'access_token': jwt_tokens["access"]}
        
        with patch('auth_app.authentication.logger'):
            token = self.auth.get_raw_token(mock_request)
            
            # Should fall back to cookie
            assert token == jwt_tokens["access"]
            
    def test_get_raw_token_no_token_available(self, mock_request):
        """Test token extraction when no token is available."""
        mock_request.META = {}
        mock_request.COOKIES = {}
        
        with patch('auth_app.authentication.logger'):
            token = self.auth.get_raw_token(mock_request)
            
            assert token is None
            
    def test_get_raw_token_empty_cookie(self, mock_request):
        """Test token extraction with empty cookie."""
        mock_request.META = {}
        mock_request.COOKIES = {'access_token': ''}
        
        with patch('auth_app.authentication.logger'):
            token = self.auth.get_raw_token(mock_request)
            
            assert token == ''
            
    def test_authenticate_success(self, mock_request, user, jwt_tokens):
        """Test successful authentication."""
        mock_request.COOKIES = {'access_token': jwt_tokens["access"]}
        
        with patch('auth_app.authentication.logger') as mock_logger:
            result = self.auth.authenticate(mock_request)
            
            assert result is not None
            authenticated_user, validated_token = result
            assert authenticated_user.id == user.id
            assert authenticated_user.email == user.email
            mock_logger.error.assert_called()
            
    def test_authenticate_no_token(self, mock_request):
        """Test authentication without token."""
        mock_request.META = {}
        mock_request.COOKIES = {}
        
        with patch('auth_app.authentication.logger') as mock_logger:
            result = self.auth.authenticate(mock_request)
            
            assert result is None
            mock_logger.error.assert_called()
            
    def test_authenticate_invalid_token(self, mock_request):
        """Test authentication with invalid token."""
        mock_request.META = {}
        mock_request.COOKIES = {'access_token': 'invalid.jwt.token'}
        
        with patch('auth_app.authentication.logger') as mock_logger:
            result = self.auth.authenticate(mock_request)
            
            assert result is None
            mock_logger.error.assert_called()
            
    def test_authenticate_expired_token(self, mock_request, user, expired_jwt_token):
        """Test authentication with expired token."""
        mock_request.META = {}
        mock_request.COOKIES = {'access_token': expired_jwt_token}
        
        with patch('auth_app.authentication.logger') as mock_logger:
            result = self.auth.authenticate(mock_request)
            
            assert result is None
            mock_logger.error.assert_called()
            
    def test_authenticate_token_validation_exception(self, mock_request, user, jwt_tokens):
        """Test authentication when token validation raises exception."""
        mock_request.COOKIES = {'access_token': jwt_tokens["access"]}
        
        with patch.object(self.auth, 'get_validated_token', side_effect=InvalidToken("Invalid token")), \
             patch('auth_app.authentication.logger') as mock_logger:
            
            result = self.auth.authenticate(mock_request)
            
            assert result is None
            mock_logger.error.assert_called()
            
    def test_authenticate_user_retrieval_exception(self, mock_request, user, jwt_tokens):
        """Test authentication when user retrieval raises exception."""
        mock_request.COOKIES = {'access_token': jwt_tokens["access"]}
        
        with patch.object(self.auth, 'get_user', side_effect=Exception("User not found")), \
             patch('auth_app.authentication.logger') as mock_logger:
            
            result = self.auth.authenticate(mock_request)
            
            assert result is None
            mock_logger.error.assert_called()
            
    def test_debug_logging_output(self, mock_request, user, jwt_tokens):
        """Test that debug logging provides useful information."""
        mock_request.META['HTTP_AUTHORIZATION'] = f'Bearer {jwt_tokens["access"]}'
        mock_request.COOKIES = {'access_token': jwt_tokens["access"], 'other_cookie': 'value'}
        
        with patch('auth_app.authentication.logger') as mock_logger:
            self.auth.get_raw_token(mock_request)
            
            # Verify logging calls contain expected information
            calls = mock_logger.error.call_args_list
            assert len(calls) >= 2  # At least 2 debug calls expected
            
            # Check that cookies are logged
            cookie_call = next((call for call in calls if 'Available cookies' in str(call)), None)
            assert cookie_call is not None
            
    def test_token_from_header_logging(self, mock_request, jwt_tokens):
        """Test logging when token comes from header."""
        mock_request.META['HTTP_AUTHORIZATION'] = f'Bearer {jwt_tokens["access"]}'
        mock_request.COOKIES = {}
        
        with patch('auth_app.authentication.logger') as mock_logger:
            self.auth.get_raw_token(mock_request)
            
            # Should log token from header
            calls = mock_logger.error.call_args_list
            header_call = next((call for call in calls if 'Token from header' in str(call)), None)
            assert header_call is not None
            
    def test_token_from_cookie_logging(self, mock_request, jwt_tokens):
        """Test logging when token comes from cookie."""
        mock_request.META = {}
        mock_request.COOKIES = {'access_token': jwt_tokens["access"]}
        
        with patch('auth_app.authentication.logger') as mock_logger:
            self.auth.get_raw_token(mock_request)
            
            # Should log token from cookie
            calls = mock_logger.error.call_args_list
            cookie_call = next((call for call in calls if 'Token from cookie' in str(call)), None)
            assert cookie_call is not None
            
    def test_authentication_success_logging(self, mock_request, user, jwt_tokens):
        """Test logging on successful authentication."""
        mock_request.COOKIES = {'access_token': jwt_tokens["access"]}
        
        with patch('auth_app.authentication.logger') as mock_logger:
            result = self.auth.authenticate(mock_request)
            
            assert result is not None
            
            # Should log successful authentication
            calls = mock_logger.error.call_args_list
            success_call = next((call for call in calls if 'Authentication SUCCESS' in str(call)), None)
            assert success_call is not None
            
    def test_authentication_failure_logging(self, mock_request):
        """Test logging on authentication failure."""
        mock_request.META = {}
        mock_request.COOKIES = {'access_token': 'invalid.token'}
        
        with patch('auth_app.authentication.logger') as mock_logger:
            result = self.auth.authenticate(mock_request)
            
            assert result is None
            
            # Should log token validation failure
            calls = mock_logger.error.call_args_list
            failure_call = next((call for call in calls if 'Token validation failed' in str(call)), None)
            assert failure_call is not None


class TestCookieJWTAuthenticationIntegration:
    """Integration tests for CookieJWTAuthentication."""
    
    def setup_method(self):
        """Set up test instance."""
        self.auth = CookieJWTAuthentication()
        
    def test_full_authentication_flow_header(self, user):
        """Test full authentication flow using header."""
        # Generate real tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Create mock request with header
        request = Mock()
        request.META = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}
        request.COOKIES = {}
        
        with patch('auth_app.authentication.logger'):
            # Test token extraction
            raw_token = self.auth.get_raw_token(request)
            assert raw_token == access_token
            
            # Test full authentication
            result = self.auth.authenticate(request)
            assert result is not None
            authenticated_user, validated_token = result
            assert authenticated_user.id == user.id
            
    def test_full_authentication_flow_cookie(self, user):
        """Test full authentication flow using cookie."""
        # Generate real tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Create mock request with cookie
        request = Mock()
        request.META = {}
        request.COOKIES = {'access_token': access_token}
        
        with patch('auth_app.authentication.logger'):
            # Test token extraction
            raw_token = self.auth.get_raw_token(request)
            assert raw_token == access_token
            
            # Test full authentication
            result = self.auth.authenticate(request)
            assert result is not None
            authenticated_user, validated_token = result
            assert authenticated_user.id == user.id
            
    def test_authentication_with_deleted_user(self, user):
        """Test authentication when user has been deleted."""
        # Generate token for user
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Delete the user
        user_id = user.id
        user.delete()
        
        # Create mock request
        request = Mock()
        request.META = {}
        request.COOKIES = {'access_token': access_token}
        
        with patch('auth_app.authentication.logger'):
            result = self.auth.authenticate(request)
            
            # Should return None because user doesn't exist anymore
            assert result is None
            