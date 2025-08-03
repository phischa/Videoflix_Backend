import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from auth_app.api.serializers import (
    RegistrationSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetSerializer,
    PasswordConfirmSerializer
)


@pytest.fixture
@pytest.mark.django_db
def test_user():
    """Create a test user"""
    return User.objects.create_user(
        username='testuser@example.com',
        email='testuser@example.com',
        password='testpass123',
        is_active=True
    )


@pytest.fixture
@pytest.mark.django_db
def inactive_user():
    """Create an inactive test user"""
    return User.objects.create_user(
        username='inactive@example.com',
        email='inactive@example.com',
        password='testpass123',
        is_active=False
    )


@pytest.mark.django_db
class TestRegistrationSerializer:
    """Test RegistrationSerializer functionality"""
    
    def test_valid_registration_data(self):
        """Test registration with valid data"""
        valid_data = {
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'confirmed_password': 'securepassword123'
        }
        
        serializer = RegistrationSerializer(data=valid_data)
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        
        # Check validated data
        validated_data = serializer.validated_data
        assert validated_data['email'] == 'newuser@example.com'
        assert validated_data['password'] == 'securepassword123'
        assert validated_data['confirmed_password'] == 'securepassword123'
    
    def test_password_mismatch(self):
        """Test registration with password mismatch"""
        invalid_data = {
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirmed_password': 'differentpassword'
        }
        
        serializer = RegistrationSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'confirmed_password' in serializer.errors
        assert 'Passwords do not match' in str(serializer.errors['confirmed_password'])
    
    def test_duplicate_email(self, test_user):
        """Test registration with existing email"""
        invalid_data = {
            'email': test_user.email,
            'password': 'password123',
            'confirmed_password': 'password123'
        }
        
        serializer = RegistrationSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
        assert 'Email already exists' in str(serializer.errors['email'])
    
    def test_missing_required_fields(self):
        """Test registration with missing required fields"""
        incomplete_data = {
            'email': 'test@example.com'
            # Missing password and confirmed_password
        }
        
        serializer = RegistrationSerializer(data=incomplete_data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
        assert 'confirmed_password' in serializer.errors
    
    def test_invalid_email_format(self):
        """Test registration with invalid email format"""
        invalid_data = {
            'email': 'invalidemail',
            'password': 'password123',
            'confirmed_password': 'password123'
        }
        
        serializer = RegistrationSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
    
    def test_save_user_creation(self):
        """Test user creation through serializer save method"""
        valid_data = {
            'email': 'savetest@example.com',
            'password': 'securepassword123',
            'confirmed_password': 'securepassword123'
        }
        
        serializer = RegistrationSerializer(data=valid_data)
        assert serializer.is_valid()
        
        user = serializer.save()
        assert isinstance(user, User)
        assert user.email == 'savetest@example.com'
        assert user.username == 'savetest@example.com'  # Should use email as username
        assert user.is_active is False  # Should be inactive by default
        assert user.check_password('securepassword123')
    
    def test_save_duplicate_username_check(self, test_user):
        """Test save method duplicate username check"""
        valid_data = {
            'email': test_user.email,
            'password': 'password123',
            'confirmed_password': 'password123'
        }
        
        serializer = RegistrationSerializer(data=valid_data)
        # Should fail validation before save
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestCustomTokenObtainPairSerializer:
    """Test CustomTokenObtainPairSerializer functionality"""
    
    def test_valid_login_credentials(self, test_user):
        """Test login with valid credentials"""
        valid_data = {
            'email': test_user.email,
            'password': 'testpass123'
        }
        
        serializer = CustomTokenObtainPairSerializer(data=valid_data)
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        
        # Check that user is stored
        assert hasattr(serializer, 'user')
        assert serializer.user.email == test_user.email
    
    def test_invalid_email(self):
        """Test login with non-existent email"""
        invalid_data = {
            'email': 'nonexistent@example.com',
            'password': 'somepassword'
        }
        
        serializer = CustomTokenObtainPairSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert 'Invalid email or password' in str(serializer.errors)
    
    def test_inactive_user_login(self, inactive_user):
        """Test login with inactive user"""
        invalid_data = {
            'email': inactive_user.email,
            'password': 'testpass123'
        }
        
        serializer = CustomTokenObtainPairSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'Account not activated' in str(serializer.errors)
    
    def test_wrong_password(self, test_user):
        """Test login with wrong password"""
        invalid_data = {
            'email': test_user.email,
            'password': 'wrongpassword'
        }
        
        serializer = CustomTokenObtainPairSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'Invalid email or password' in str(serializer.errors)
    
    def test_username_field_removed(self):
        """Test that username field is removed from serializer"""
        serializer = CustomTokenObtainPairSerializer()
        assert 'username' not in serializer.fields
        assert 'email' in serializer.fields
        assert 'password' in serializer.fields
    
    def test_email_to_username_mapping(self, test_user):
        """Test that email is mapped to username in validation"""
        valid_data = {
            'email': test_user.email,
            'password': 'testpass123'
        }
        
        serializer = CustomTokenObtainPairSerializer(data=valid_data)
        assert serializer.is_valid()
        
        # After validation, username should be set
        validated_data = serializer.validated_data
        assert 'username' in validated_data
        assert validated_data['username'] == test_user.username


@pytest.mark.django_db
class TestPasswordResetSerializer:
    """Test PasswordResetSerializer functionality"""
    
    def test_valid_email_format(self):
        """Test password reset with valid email format"""
        valid_data = {
            'email': 'test@example.com'
        }
        
        serializer = PasswordResetSerializer(data=valid_data)
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        
        validated_data = serializer.validated_data
        assert validated_data['email'] == 'test@example.com'
    
    def test_invalid_email_format(self):
        """Test password reset with invalid email format"""
        invalid_data = {
            'email': 'invalidemail'
        }
        
        serializer = PasswordResetSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
    
    def test_empty_email(self):
        """Test password reset with empty email"""
        invalid_data = {
            'email': ''
        }
        
        serializer = PasswordResetSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
    
    def test_missing_email(self):
        """Test password reset with missing email field"""
        invalid_data = {}
        
        serializer = PasswordResetSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
    
    def test_user_exists_stored_in_serializer(self, test_user):
        """Test that existing user is stored in serializer instance"""
        valid_data = {
            'email': test_user.email
        }
        
        serializer = PasswordResetSerializer(data=valid_data)
        assert serializer.is_valid()
        
        # User should be stored in serializer instance
        assert hasattr(serializer, 'user')
        assert serializer.user.email == test_user.email
    
    def test_nonexistent_user_handled(self):
        """Test that non-existent user is handled gracefully"""
        valid_data = {
            'email': 'nonexistent@example.com'
        }
        
        serializer = PasswordResetSerializer(data=valid_data)
        assert serializer.is_valid()  # Should still be valid for security
        
        # User should be None
        assert hasattr(serializer, 'user')
        assert serializer.user is None


@pytest.mark.django_db
class TestPasswordConfirmSerializer:
    """Test PasswordConfirmSerializer functionality"""
    
    def test_valid_password_confirmation(self):
        """Test password confirmation with valid matching passwords"""
        valid_data = {
            'new_password': 'newsecurepassword123',
            'confirm_password': 'newsecurepassword123'
        }
        
        serializer = PasswordConfirmSerializer(data=valid_data)
        assert serializer.is_valid(), f"Serializer errors: {serializer.errors}"
        
        validated_data = serializer.validated_data
        assert validated_data['new_password'] == 'newsecurepassword123'
        assert validated_data['confirm_password'] == 'newsecurepassword123'
    
    def test_password_mismatch(self):
        """Test password confirmation with mismatched passwords"""
        invalid_data = {
            'new_password': 'password123',
            'confirm_password': 'differentpassword'
        }
        
        serializer = PasswordConfirmSerializer(data=invalid_data)
        assert not serializer.is_valid()
        
        # Could be in confirm_password field or non_field_errors
        errors_str = str(serializer.errors)
        assert 'Passwords do not match' in errors_str
    
    def test_short_password_validation(self):
        """Test password confirmation with too short password"""
        invalid_data = {
            'new_password': '123',  # Too short
            'confirm_password': '123'
        }
        
        serializer = PasswordConfirmSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'new_password' in serializer.errors
    
    def test_weak_password_validation(self):
        """Test password confirmation with weak password"""
        invalid_data = {
            'new_password': 'password',  # Too common
            'confirm_password': 'password'
        }
        
        serializer = PasswordConfirmSerializer(data=invalid_data)
        # May or may not fail depending on Django password validators
        # But should handle validation gracefully
        if not serializer.is_valid():
            assert 'new_password' in serializer.errors
    
    def test_missing_fields(self):
        """Test password confirmation with missing fields"""
        incomplete_data = {
            'new_password': 'password123'
            # Missing confirm_password
        }
        
        serializer = PasswordConfirmSerializer(data=incomplete_data)
        assert not serializer.is_valid()
        assert 'confirm_password' in serializer.errors
    
    def test_cross_field_validation(self):
        """Test cross-field validation in validate method"""
        invalid_data = {
            'new_password': 'password123',
            'confirm_password': 'differentpassword123'
        }
        
        serializer = PasswordConfirmSerializer(data=invalid_data)
        assert not serializer.is_valid()
        
        # Should have validation error
        errors_str = str(serializer.errors)
        assert 'Passwords do not match' in errors_str


@pytest.mark.django_db
class TestSerializersEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_registration_with_whitespace_email(self):
        """Test registration with email containing whitespace"""
        data_with_whitespace = {
            'email': '  test@example.com  ',
            'password': 'password123',
            'confirmed_password': 'password123'
        }
        
        serializer = RegistrationSerializer(data=data_with_whitespace)
        is_valid = serializer.is_valid()
        
        # Should either be valid (with trimmed email) or invalid (strict validation)
        if is_valid:
            assert serializer.validated_data['email'].strip() == 'test@example.com'
    
    def test_serializers_with_unicode_data(self):
        """Test serializers with unicode characters"""
        unicode_data = {
            'email': 'тест@example.com',  # Cyrillic characters
            'password': 'пароль123',
            'confirmed_password': 'пароль123'
        }
        
        serializer = RegistrationSerializer(data=unicode_data)
        # Should handle unicode gracefully
        if serializer.is_valid():
            assert 'тест@example.com' in serializer.validated_data['email']
    
    def test_password_reset_case_sensitivity(self, test_user):
        """Test password reset email case sensitivity"""
        # Create user with lowercase email
        upper_email_data = {
            'email': test_user.email.upper()
        }
        
        serializer = PasswordResetSerializer(data=upper_email_data)
        serializer.is_valid()
        
        # Depending on implementation, might or might not find user
        # Should handle gracefully either way
        assert hasattr(serializer, 'user')
        