import jwt
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import authentication, exceptions
from drf_spectacular.extensions import OpenApiAuthenticationExtension

class JWTAuthentication(authentication.BaseAuthentication):
    """
    Custom JWT authentication backend for Django REST Framework.

    Clients should authenticate by passing the token key in the 'Authorization'
    HTTP header, prepended with the string 'Bearer '. For example:
        Authorization: Bearer <your_jwt_access_token>
    """

    def authenticate(self, request):
        """
        Authenticates the request by validating the JWT token from the header.
        """
        auth_header = authentication.get_authorization_header(request).split()

        if not auth_header or auth_header[0].lower() != b'bearer':
            return None

        if len(auth_header) == 1:
            raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')
        elif len(auth_header) > 2:
            raise exceptions.AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

        try:
            token = auth_header[1].decode('utf-8')
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            
            if payload.get('token_type') != 'access':
                raise exceptions.AuthenticationFailed('Invalid token type. Only access tokens are allowed.')

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired.')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token.')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {e}')

        try:
            user = User.objects.get(pk=payload['user_id'])
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No user matching this token was found.')

        return (user, token)
    
    def authenticate_header(self, request):
        return 'Bearer'

class JWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    Extension for drf-spectacular to correctly document the custom JWT authentication.
    """
    target_class = 'users.authentication.JWTAuthentication'
    name = 'JWT Bearer Auth'

    def get_security_definition(self, auto_schema):
        """
        Returns the OpenAPI security scheme definition for HTTP Bearer authentication.
        """
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Enter your JWT in the format: Bearer {token}'
        }
