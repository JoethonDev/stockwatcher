from django.contrib.auth.models import User
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse

import jwt

from .serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    TokenSerializer,
    RefreshTokenSerializer,
    UserDetailSerializer
)
from .utils import generate_tokens, decode_jwt
from .permissions import IsNotAuthenticated


@extend_schema(
    tags=["Authentication"],
    summary="Register a new user",
    description="Create a new user account. Only available for unauthenticated users.",
    request=UserRegistrationSerializer,
    responses={
        201: OpenApiResponse(response=UserRegistrationSerializer, description="User created successfully"),
        400: OpenApiResponse(description="Invalid input data"),
        403: OpenApiResponse(description="Already authenticated"),
    }
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsNotAuthenticated]


@extend_schema(
    tags=["Authentication"],
    summary="Login and obtain JWT tokens",
    description="Authenticate user and return JWT access & refresh tokens.",
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(response=TokenSerializer, description="Tokens returned successfully"),
        400: OpenApiResponse(description="Invalid input"),
        401: OpenApiResponse(description="Invalid credentials"),
        403: OpenApiResponse(description="Already authenticated"),
    }
)
class LoginView(APIView):
    permission_classes = [IsNotAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        tokens = generate_tokens(user)
        return Response(TokenSerializer(tokens).data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Authentication"],
    summary="Refresh JWT access token",
    description="Submit a valid refresh token to obtain a new access & refresh token pair.",
    request=RefreshTokenSerializer,
    responses={
        200: OpenApiResponse(response=TokenSerializer, description="New tokens issued"),
        401: OpenApiResponse(description="Invalid or expired refresh token"),
        403: OpenApiResponse(description="Already authenticated"),
    }
)
class RefreshTokenView(APIView):
    permission_classes = [IsNotAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data['refresh']

        try:
            payload = decode_jwt(refresh_token)
            if payload.get('token_type') != 'refresh':
                return Response({'detail': 'Invalid token type.'}, status=status.HTTP_401_UNAUTHORIZED)

            user = User.objects.get(id=payload['user_id'])
            tokens = generate_tokens(user)
            return Response(TokenSerializer(tokens).data, status=status.HTTP_200_OK)

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return Response({'detail': 'Token is invalid or expired.'}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(
    tags=["Authentication"],
    summary="Get user profile",
    description="Retrieve profile details of the currently authenticated user.",
    responses={
        200: OpenApiResponse(response=UserDetailSerializer, description="User profile data"),
        401: OpenApiResponse(description="Authentication required"),
    }
)
class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
