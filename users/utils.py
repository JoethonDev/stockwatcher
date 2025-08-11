# users/utils.py
from uuid import uuid4
import jwt
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User

def generate_tokens(user: User) -> dict:
    """
    Generates a pair of access and refresh tokens for a given user.

    Args:
        user (User): The user object for whom to generate tokens.

    Returns:
        dict: A dictionary containing the 'access' and 'refresh' tokens.
    """
    access_payload = {
        'token_type': 'access',
        'user_id': user.id,
        'username': user.username,
        'exp': timezone.now() + timedelta(minutes=settings.ACCESS_TOKEN_LIFETIME_MINUTES),
        'iat': timezone.now(),
        'jti': str(uuid4()),
    }
    access_token = jwt.encode(access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    refresh_payload = {
        'token_type': 'refresh',
        'user_id': user.id,
        'exp': timezone.now() + timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS),
        'iat': timezone.now(),
        'jti': str(uuid4()),
    }
    refresh_token = jwt.encode(refresh_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return {
        'access': access_token,
        'refresh': refresh_token
    }

def decode_jwt(token: str) -> dict:
    """
    Decodes and validates a JWT token.

    Args:
        token (str): The JWT token string to decode.

    Returns:
        dict: The decoded token payload if the token is valid.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is malformed or the signature is invalid.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
