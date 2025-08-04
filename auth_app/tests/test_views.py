import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from unittest.mock import patch, Mock
import json


class TestHelloWorldView:
    """Tests for HelloWorldView."""
    
    def test_hello_world_authenticated_success(self, authenticated_client):
        """Test HelloWorldView with authenticated user."""
        url = reverse('hello')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Hello World!'
        
    def test_hello_world_unauthenticated_fails(self, api_client):
        """Test HelloWorldView without authentication."""
        url = reverse('hello')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRegistrationView:
    """Tests for RegistrationView."""
    
    def test_registration_success(self, api_client, registration_data, mock_email_sent):
        """Test successful user registration."""
        url = reverse('register')
        response = api_client.post(url, registration_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert response.data['user']['email'] == registration_data['email']
        assert response.data['email_sent'] is True
        assert 'Account created' in response.data['message']
        
        # Verify user was created
        user = User.objects.get(email=registration_data['email'])
        assert user.email == registration_data['email']
        assert user.is_active is False  # Should be inactive until activation
        
        # Verify email sending was called
        mock_email_sent['activation'].assert_called_once()
        
    def test_registration_email_failure(self, api_client, registration_data):
        """Test registration when email sending fails."""
        with patch('auth_app.api.views.send_activation_email', return_value=False):
            url = reverse('register')
            response = api_client.post(url, registration_data, format='json')
            
            assert response.status_code == status.HTTP_201_CREATED
            assert response.data['email_sent'] is False
            assert 'contact support' in response.data['message']
    
    def test_registration_password_mismatch(self, api_client):
        """Test registration with password mismatch."""
        data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'confirmed_password': 'DifferentPassword123!'
        }
        url = reverse('register')
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'confirmed_password' in response.data
        
    def test_registration_duplicate_email(self, api_client, user, user_data):
        """Test registration with existing email."""
        url = reverse('register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
        
    def test_registration_invalid_email(self, api_client):
        """Test registration with invalid email."""
        data = {
            'email': 'invalid-email',
            'password': 'TestPassword123!',
            'confirmed_password': 'TestPassword123!'
        }
        url = reverse('register')
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
        
    def test_registration_missing_fields(self, api_client):
        """Test registration with missing required fields."""
        data = {
            'email': 'test@example.com'
            # Missing password fields
        }
        url = reverse('register')
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data


class TestLogoutView:
    """Tests for LogoutView."""
    
    def test_logout_success(self, api_client, user, jwt_tokens):
        """Test successful logout."""
        api_client.cookies['refresh_token'] = jwt_tokens['refresh']
        
        with patch('rest_framework_simplejwt.tokens.RefreshToken.blacklist') as mock_blacklist:
            url = reverse('logout')
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert 'Log-Out successfully' in response.data['detail']
            mock_blacklist.assert_called_once()
            
            # Check cookies are deleted
            assert response.cookies['access_token'].value == ''
            assert response.cookies['refresh_token'].value == ''
    
    def test_logout_missing_refresh_token(self, api_client):
        """Test logout without refresh token."""
        url = reverse('logout')
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Refresh token not found' in response.data['detail']
        
    def test_logout_invalid_refresh_token(self, api_client):
        """Test logout with invalid refresh token."""
        api_client.cookies['refresh_token'] = 'invalid.token'
        
        url = reverse('logout')
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid refresh token' in response.data['detail']


class TestCookieTokenObtainPairView:
    """Tests for CookieTokenObtainPairView."""
    
    def test_login_success(self, api_client, user, login_data):
        """Test successful login."""
        url = reverse('token_obtain_pair')
        response = api_client.post(url, login_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Login successful' in response.data['detail']
        assert 'user' in response.data
        assert response.data['user']['username'] == user.email
        
        # Check cookies are set
        assert 'access_token' in response.cookies
        assert 'refresh_token' in response.cookies
        assert response.cookies['access_token']['httponly'] is True
        
    def test_login_inactive_user(self, api_client, inactive_user):
        """Test login with inactive user."""
        data = {
            'email': inactive_user.email,
            'password': 'TestPassword123!'
        }
        url = reverse('token_obtain_pair')
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Account not activated' in str(response.data)
        
    def test_login_invalid_credentials(self, api_client, user):
        """Test login with invalid credentials."""
        data = {
            'email': user.email,
            'password': 'WrongPassword123!'
        }
        url = reverse('token_obtain_pair')
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_login_nonexistent_user(self, api_client):
        """Test login with non-existent user."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'SomePassword123!'
        }
        url = reverse('token_obtain_pair')
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_login_missing_fields(self, api_client):
        """Test login with missing fields."""
        data = {
            'email': 'test@example.com'
            # Missing password
        }
        url = reverse('token_obtain_pair')
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCookieTokenRefreshView:
    """Tests for CookieTokenRefreshView."""
    
    def test_token_refresh_success(self, api_client, user, jwt_tokens):
        """Test successful token refresh."""
        api_client.cookies['refresh_token'] = jwt_tokens['refresh']
        
        url = reverse('token_refresh')
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Token refreshed' in response.data['detail']
        assert response.data['access'] == "new_access_token"  # Literal string from view
        
        # Check new access token cookie is set
        assert 'access_token' in response.cookies
        
    def test_token_refresh_missing_token(self, api_client):
        """Test token refresh without refresh token."""
        url = reverse('token_refresh')
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Refresh token missing' in response.data['detail']
        
    def test_token_refresh_invalid_token(self, api_client):
        """Test token refresh with invalid token."""
        api_client.cookies['refresh_token'] = 'invalid.token'
        
        url = reverse('token_refresh')
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Refresh token invalid' in response.data['detail']


class TestAccountActivationView:
    """Tests for AccountActivationView."""
    
    def test_activation_success(self, api_client, inactive_user, sample_uid_token, mock_token_services):
        """Test successful account activation."""
        mock_token_services['verify_activation'].return_value = inactive_user
        
        url = reverse('account_activate',
                      kwargs={'uidb64': sample_uid_token['uidb64'],
                              'token': sample_uid_token['token']})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Account successfully activated' in response.data['message']
        
        mock_token_services['verify_activation'].assert_called_once_with(
            sample_uid_token['uidb64'], sample_uid_token['token']
        )
        mock_token_services['activate_user'].assert_called_once_with(inactive_user)
        
    def test_activation_already_active_user(self, api_client, user, sample_uid_token, mock_token_services):
        """Test activation of already active user."""
        mock_token_services['verify_activation'].return_value = user
        
        url = reverse('account_activate',
                      kwargs={'uidb64': sample_uid_token['uidb64'],
                              'token': sample_uid_token['token']})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Account successfully activated' in response.data['message']
        
        # activate_user should not be called for already active user
        mock_token_services['activate_user'].assert_not_called()
        
    def test_activation_invalid_token(self, api_client, sample_uid_token, mock_token_services):
        """Test activation with invalid token."""
        mock_token_services['verify_activation'].return_value = None
        
        url = reverse('account_activate',
                      kwargs={'uidb64': sample_uid_token['uidb64'],
                              'token': sample_uid_token['token']})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid or expired activation link' in response.data['detail']
        
    def test_activation_service_failure(self, api_client, inactive_user, sample_uid_token, mock_token_services):
        """Test activation when service fails."""
        mock_token_services['verify_activation'].return_value = inactive_user
        mock_token_services['activate_user'].return_value = False
        
        url = reverse('account_activate',
                      kwargs={'uidb64': sample_uid_token['uidb64'],
                              'token': sample_uid_token['token']})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'Failed to activate account' in response.data['detail']


class TestPasswordResetView:
    """Tests for PasswordResetView."""
    
    def test_password_reset_success(self, api_client, user, password_reset_data, mock_email_sent):
        """Test successful password reset request."""
        with patch('auth_app.api.views.PasswordResetSerializer') as mock_serializer_class:
            mock_serializer = Mock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.user = user
            mock_serializer_class.return_value = mock_serializer
            
            url = reverse('password_reset')
            response = api_client.post(url, password_reset_data, format='json')
            
            assert response.status_code == status.HTTP_200_OK
            assert 'email has been sent' in response.data['detail']
            mock_email_sent['reset'].assert_called_once()
    
    def test_password_reset_nonexistent_user(self, api_client, password_reset_data):
        """Test password reset for non-existent user."""
        # Should still return success for security reasons
        url = reverse('password_reset')
        response = api_client.post(url, password_reset_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'email has been sent' in response.data['detail']
        
    def test_password_reset_invalid_email(self, api_client):
        """Test password reset with invalid email."""
        data = {'email': 'invalid-email'}
        url = reverse('password_reset')
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_password_reset_email_failure(self, api_client, user, password_reset_data):
        """Test password reset when email sending fails."""
        with patch('auth_app.api.views.PasswordResetSerializer') as mock_serializer_class, \
             patch('auth_app.api.views.send_password_reset_email', return_value=False):
            
            mock_serializer = Mock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.user = user
            mock_serializer_class.return_value = mock_serializer
            
            url = reverse('password_reset')
            response = api_client.post(url, password_reset_data, format='json')
            
            # Should still return success message for security
            assert response.status_code == status.HTTP_200_OK
            assert 'email has been sent' in response.data['detail']


class TestPasswordConfirmView:
    """Tests for PasswordConfirmView."""
    
    def test_password_confirm_success(self, api_client, user, sample_uid_token, 
                                     password_confirm_data, mock_token_services):
        """Test successful password confirmation."""
        mock_token_services['verify_reset'].return_value = user
        
        url = reverse('password_confirm',
                      kwargs={'uidb64': sample_uid_token['uidb64'],
                              'token': sample_uid_token['token']})
        response = api_client.post(url, password_confirm_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'password has been successfully reset' in response.data['detail']
        
        mock_token_services['verify_reset'].assert_called_once_with(
            sample_uid_token['uidb64'], sample_uid_token['token']
        )
        mock_token_services['reset_password'].assert_called_once_with(
            user, password_confirm_data['new_password']
        )
        
    def test_password_confirm_invalid_token(self, api_client, sample_uid_token, 
                                           password_confirm_data, mock_token_services):
        """Test password confirmation with invalid token."""
        mock_token_services['verify_reset'].return_value = None
        
        url = reverse('password_confirm',
                      kwargs={'uidb64': sample_uid_token['uidb64'],
                              'token': sample_uid_token['token']})
        response = api_client.post(url, password_confirm_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid or expired password reset link' in response.data['detail']
        
    def test_password_confirm_invalid_password(self, api_client, user, sample_uid_token, mock_token_services):
        """Test password confirmation with invalid password data."""
        mock_token_services['verify_reset'].return_value = user
        
        invalid_data = {
            'new_password': '123',  # Too short
            'confirm_password': '123'
        }
        
        url = reverse('password_confirm',
                      kwargs={'uidb64': sample_uid_token['uidb64'],
                              'token': sample_uid_token['token']})
        response = api_client.post(url, invalid_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_password_confirm_service_failure(self, api_client, user, sample_uid_token, 
                                             password_confirm_data, mock_token_services):
        """Test password confirmation when service fails."""
        mock_token_services['verify_reset'].return_value = user
        mock_token_services['reset_password'].return_value = False
        
        url = reverse('password_confirm',
                      kwargs={'uidb64': sample_uid_token['uidb64'],
                              'token': sample_uid_token['token']})
        response = api_client.post(url, password_confirm_data, format='json')
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'Failed to reset password' in response.data['detail']


class TestViewsIntegration:
    """Integration tests for auth views."""
    
    def test_full_registration_activation_flow(self, api_client, registration_data, mock_token_services, mock_email_sent):
        """Test complete registration and activation flow."""
        # Step 1: Register
        url = reverse('register')
        response = api_client.post(url, registration_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Step 2: User should be inactive
        user = User.objects.get(email=registration_data['email'])
        assert user.is_active is False
        
        # Step 3: Activate account
        mock_token_services['verify_activation'].return_value = user
        activation_url = reverse('account_activate',
                               kwargs={'uidb64': 'test64', 'token': 'testtoken'})
        response = api_client.get(activation_url)
        assert response.status_code == status.HTTP_200_OK
        
    def test_full_password_reset_flow(self, api_client, user, password_reset_data, 
                                     password_confirm_data, mock_token_services, mock_email_sent):
        """Test complete password reset flow."""
        # Step 1: Request password reset
        with patch('auth_app.api.views.PasswordResetSerializer') as mock_serializer_class:
            mock_serializer = Mock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.user = user
            mock_serializer_class.return_value = mock_serializer
            
            reset_url = reverse('password_reset')
            response = api_client.post(reset_url, password_reset_data, format='json')
            assert response.status_code == status.HTTP_200_OK
        
        # Step 2: Confirm password reset
        mock_token_services['verify_reset'].return_value = user
        confirm_url = reverse('password_confirm',
                             kwargs={'uidb64': 'test64', 'token': 'testtoken'})
        response = api_client.post(confirm_url, password_confirm_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
    def test_login_logout_flow(self, api_client, user, login_data):
        """Test complete login and logout flow."""
        # Step 1: Login
        login_url = reverse('token_obtain_pair')
        response = api_client.post(login_url, login_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Extract refresh token from cookies
        refresh_token = response.cookies['refresh_token'].value
        api_client.cookies['refresh_token'] = refresh_token
        
        # Step 2: Logout
        with patch('rest_framework_simplejwt.tokens.RefreshToken.blacklist'):
            logout_url = reverse('logout')
            response = api_client.post(logout_url)
            assert response.status_code == status.HTTP_200_OK
            
    def test_token_refresh_flow(self, api_client, user, login_data):
        """Test login and token refresh flow."""
        # Step 1: Login
        login_url = reverse('token_obtain_pair')
        response = api_client.post(login_url, login_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Extract refresh token
        refresh_token = response.cookies['refresh_token'].value
        api_client.cookies['refresh_token'] = refresh_token
        
        # Step 2: Refresh token
        refresh_url = reverse('token_refresh')
        response = api_client.post(refresh_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['access'] == "new_access_token"  # Literal string from view


class TestViewsErrorHandling:
    """Tests for error handling across views."""
    
    def test_invalid_http_methods(self, api_client):
        """Test views with invalid HTTP methods."""
        # RegistrationView should only accept POST
        url = reverse('register')
        response = api_client.get(url)
        # Could be 405 (Method Not Allowed) or 401 (Unauthorized)
        assert response.status_code in [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_401_UNAUTHORIZED]
        
        # HelloWorldView should only accept GET - and requires authentication
        hello_url = reverse('hello')
        response = api_client.post(hello_url)
        # Will likely be 401 since authentication is required first
        assert response.status_code in [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_401_UNAUTHORIZED]
        
    def test_malformed_json_requests(self, api_client):
        """Test views with malformed JSON."""
        url = reverse('register')
        response = api_client.post(url, 'invalid json', content_type='application/json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_empty_request_bodies(self, api_client):
        """Test views with empty request bodies."""
        url = reverse('register')
        response = api_client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_view_permissions_enforcement(self, api_client):
        """Test that view permissions are properly enforced."""
        # HelloWorldView requires authentication
        url = reverse('hello')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Public views should work without authentication
        public_urls = [
            reverse('register'),
            reverse('token_obtain_pair'),
            reverse('password_reset'),
        ]
        
        for url in public_urls:
            # Should not return 401 for GET requests (might return 405 for method not allowed)
            response = api_client.options(url)  # OPTIONS should work for CORS
            assert response.status_code != status.HTTP_401_UNAUTHORIZED
            