from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
    

class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with email and password confirmation.
    
    Creates inactive users that require email activation.
    """
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'email': {
                'required': True
            }
        }

    def validate_confirmed_password(self, value):
        """Validates that confirmed password matches the main password."""
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def validate_email(self, value):
        """Validates that email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def save(self):
        """Creates new inactive user account with email as username."""
        pw = self.validated_data['password']
        email = self.validated_data['email']

        if User.objects.filter(username=email).exists():
            raise serializers.ValidationError({'email': 'User with this email already exists'})
        
        account = User(
            email=email,
            username=email,
            is_active=False
        )
        account.set_password(pw)
        account.save()
        return account


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer for email-based login instead of username.
    
    Validates account activation status before issuing tokens.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):   
        """Removes username field since we use email for authentication."""
        super().__init__(*args, **kwargs)   

        if "username" in self.fields:
            self.fields.pop("username")

    def validate(self, attrs):
        """
        Validates login credentials and account activation status.
        
        Returns JWT tokens for valid, active accounts.
        """
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")
        
        if not user.is_active:
            raise serializers.ValidationError("Account not activated. Please check your email for activation link.")
        
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password")
        
        self.user = user

        attrs['username'] = user.username
        data = super().validate(attrs)
        return data
    

class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for password reset request
    Used for: POST /api/password_reset/
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        """
        Validate email format and check if user exists
        Note: For security reasons, not revealing if user exists or not
        """
        # Basic email format validation (already done by EmailField)
        if not value:
            raise serializers.ValidationError('Email is required')
        
        # Store the user for later use if exists (but don't reveal if not)
        try:
            user = User.objects.get(email=value)
            self.user = user
        except User.DoesNotExist:
            self.user = None
        
        return value


class PasswordConfirmSerializer(serializers.Serializer):
    """
    Serializer for password confirmation/reset
    Used for: POST /api/password_confirm/<uidb64>/<token>/
    """
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_new_password(self, value):
        """Validate new password using Django's built-in validators"""
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value

    def validate_confirm_password(self, value):
        """Validate password confirmation matches new password"""
        new_password = self.initial_data.get('new_password')
        if new_password and value and new_password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def validate(self, attrs):
        """Cross-field validation to ensure passwords match"""
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        if new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })
        
        return attrs
