from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from alerts.serializers import AlertListSerializer
from rest_framework.exceptions import AuthenticationFailed, ValidationError


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Handles user registration and password hashing.
    """
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="User password"
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'password')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise ValidationError("A user with this username already exists.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )


class LoginSerializer(serializers.Serializer):
    """
    Authenticates user credentials for token retrieval.
    """
    username = serializers.CharField(
        required=True,
        help_text="Your username"
    )
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        help_text="Your password"
    )

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise ValidationError("Both username and password are required.")

        user = authenticate(username=username, password=password)

        if not user:
            raise AuthenticationFailed("Invalid username or password.", code="authorization")

        if not user.is_active:
            raise AuthenticationFailed("This account is inactive.", code="authorization")

        attrs['user'] = user
        return attrs


class TokenSerializer(serializers.Serializer):
    """
    Returns access and refresh JWT tokens.
    """
    access = serializers.CharField(
        read_only=True,
        help_text="JWT access token"
    )
    refresh = serializers.CharField(
        read_only=True,
        help_text="JWT refresh token"
    )


class RefreshTokenSerializer(serializers.Serializer):
    """
    Accepts a refresh token to issue new access token.
    """
    refresh = serializers.CharField(
        required=True,
        help_text="JWT refresh token to obtain new access token"
    )


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Returns user profile details including related alerts.
    """
    alerts = AlertListSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'alerts')
