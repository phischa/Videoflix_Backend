import pytest
from django.contrib.auth.models import User
from django.test import Client
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import Mock, patch


@pytest.fixture
def api_client():
    """API client for testing DRF views."""
    return APIClient()


@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def user_data():
    """Sample user data for testing."""
    return {
        'email': 'testuser@example.com',
        'password': 'TestPassword123!',
        'confirmed_password': 'TestPassword123!'
    }


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser@example.com',
        email='testuser@example.com',
        password='TestPassword123!',
        is_active=True
    )


@pytest.fixture
def inactive_user(db):
    """Create an inactive test user."""
    return User.objects.create_user(
        username='inactive@example.com',
        email='inactive@example.com', 
        password='TestPassword123!',
        is_active=False
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        username='admin@example.com',
        email='admin@example.com',
        password='AdminPassword123!'
    )


@pytest.fixture
def jwt_tokens(user):
    """Generate JWT tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }


@pytest.fixture
def authenticated_client(api_client, user, jwt_tokens):
    """API client with authenticated user via cookies."""
    api_client.cookies['access_token'] = jwt_tokens['access']
    api_client.cookies['refresh_token'] = jwt_tokens['refresh']
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def mock_request():
    """Mock request object for testing."""
    request = Mock()
    request.META = {}
    request.COOKIES = {}
    return request


@pytest.fixture
def password_reset_data():
    """Password reset request data."""
    return {
        'email': 'testuser@example.com'
    }


@pytest.fixture
def password_confirm_data():
    """Password confirmation data."""
    return {
        'new_password': 'NewPassword123!',
        'confirm_password': 'NewPassword123!'
    }


@pytest.fixture
def registration_data():
    """Registration data for testing."""
    return {
        'email': 'newuser@example.com',
        'password': 'NewPassword123!',
        'confirmed_password': 'NewPassword123!'
    }


@pytest.fixture
def login_data():
    """Login data for testing."""
    return {
        'email': 'testuser@example.com',
        'password': 'TestPassword123!'
    }


@pytest.fixture
def mock_email_sent():
    """Mock email sending functions."""
    with patch('auth_app.api.views.send_activation_email', return_value=True) as mock_activation, \
         patch('auth_app.api.views.send_password_reset_email', return_value=True) as mock_reset:
        yield {
            'activation': mock_activation,
            'reset': mock_reset
        }


@pytest.fixture
def mock_token_services():
    """Mock token-related services."""
    with patch('auth_app.api.views.verify_activation_token') as mock_verify_activation, \
         patch('auth_app.api.views.activate_user', return_value=True) as mock_activate, \
         patch('auth_app.api.views.verify_password_reset_token') as mock_verify_reset, \
         patch('auth_app.api.views.reset_user_password', return_value=True) as mock_reset_password:
        yield {
            'verify_activation': mock_verify_activation,
            'activate_user': mock_activate,
            'verify_reset': mock_verify_reset,
            'reset_password': mock_reset_password
        }


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Grants database access to all tests automatically.
    """
    pass


@pytest.fixture
def invalid_jwt_token():
    """Invalid JWT token for testing."""
    return 'invalid.jwt.token'


@pytest.fixture
def expired_jwt_token(user):
    """Expired JWT token for testing."""
    refresh = RefreshToken.for_user(user)
    # Set expiration to past time
    from datetime import timedelta
    refresh.access_token.set_exp(lifetime=timedelta(seconds=-1))  # Already expired
    return str(refresh.access_token)


@pytest.fixture
def sample_uid_token():
    """Sample UID and token for activation/reset testing."""
    return {
        'uidb64': 'dGVzdHVpZA',  # base64 encoded 'testuid'
        'token': 'abc123-def456-ghi789'
    }
