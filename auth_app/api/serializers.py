from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
    

class RegistrationSerializer(serializers.ModelSerializer):
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
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def save(self):
        pw = self.validated_data['password']
        email = self.validated_data['email']

        # USERNAME AUS EMAIL GENERIEREN (unique)
        # Prüfe ob User mit dieser Email als Username bereits existiert
        if User.objects.filter(username=email).exists():
            raise serializers.ValidationError({'email': 'User with this email already exists'})
        
        account = User(
            email=email,
            username=email  # Email als Username verwenden
        )
        account.set_password(pw)
        account.save()
        return account


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):   
        super().__init__(*args, **kwargs)   

        if "username" in self.fields:
            self.fields.pop("username")

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")
        
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password")
        
        attrs['username'] = user.username
        data = super().validate(attrs)
        return data