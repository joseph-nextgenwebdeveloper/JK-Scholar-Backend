"""
Serializers for accounts app.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for reading and updating authenticated user information.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'school', 'degree', 'profile_photo', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Enforces password validation, confirmation, and uniqueness.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'school', 'degree', 'profile_photo')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'school': {'required': False},
            'degree': {'required': False},
            'profile_photo': {'required': False},
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({"detail": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            school=validated_data.get('school', ''),
            degree=validated_data.get('degree', ''),
            profile_photo=validated_data.get('profile_photo', 'avatar1')
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT login serializer that includes user data in the response payload.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class LogoutSerializer(serializers.Serializer):
    """
    Serializer to blacklist refresh token on logout.
    """
    refresh = serializers.CharField(required=True)

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            raise serializers.ValidationError({"detail": "Token is invalid or already expired."})
