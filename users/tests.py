from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .utils import generate_tokens

class BaseUserTestCase(APITestCase):
    """
    A base test case that sets up reusable data for user-related tests.
    This includes creating test users and an authenticated API client.
    """
    def setUp(self):
        """
        This method is run before each test function.
        """
        # Create a primary test user
        self.user_data = {'username': 'testuser', 'password': 'StrongPassword123!'}
        self.user = User.objects.create_user(**self.user_data)

        # Create a second user for ownership tests
        self.other_user_data = {'username': 'otheruser', 'password': 'OtherPassword123!'}
        self.other_user = User.objects.create_user(**self.other_user_data)

        # Create an API client instance
        self.client = APIClient()

    def authenticate_client(self, user):
        """
        Helper method to authenticate the client for a given user.
        """
        tokens = generate_tokens(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')

    def unauthenticate_client(self):
        """
        Helper method to remove authentication credentials from the client.
        """
        self.client.credentials()


class AuthEndpointTests(BaseUserTestCase):
    """
    Tests for the authentication endpoints: /register, /token, /token/refresh.
    """
    def test_register_new_user_success(self):
        """
        Ensure a new user can be registered successfully.
        """
        self.unauthenticate_client()
        new_user_data = {'username': 'newbie', 'password': 'NewPassword123!'}
        response = self.client.post('/api/users/register/', new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(response.data['username'], 'newbie')

    def test_register_fails_if_already_authenticated(self):
        """
        Ensure an already logged-in user cannot access the register endpoint.
        """
        self.authenticate_client(self.user)
        new_user_data = {'username': 'newbie', 'password': 'NewPassword123!'}
        response = self.client.post('/api/users/register/', new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_fails_with_duplicate_username(self):
        """
        Ensure registration fails if the username already exists.
        """
        self.unauthenticate_client()
        response = self.client.post('/api/users/register/', self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """
        Ensure a user can log in with correct credentials and receive tokens.
        """
        self.unauthenticate_client()
        response = self.client.post('/api/users/login/', self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_fails_with_invalid_credentials(self):
        """
        Ensure login fails with incorrect credentials.
        """
        self.unauthenticate_client()
        invalid_data = {'username': 'testuser', 'password': 'wrongpassword'}
        response = self.client.post('/api/users/login/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_token_refresh_success(self):
        """
        Ensure a new token pair can be obtained with a valid refresh token.
        """
        self.unauthenticate_client()
        tokens = generate_tokens(self.user)
        response = self.client.post('/api/users/token/refresh/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        # The new refresh token should be different from the old one (rotation)
        self.assertNotEqual(tokens['refresh'], response.data['refresh'])

    def test_token_refresh_fails_with_invalid_token(self):
        """
        Ensure token refresh fails with a malformed or invalid refresh token.
        """
        self.unauthenticate_client()
        response = self.client.post('/api/users/token/refresh/', {'refresh': 'invalidtoken'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileEndpointTests(BaseUserTestCase):
    """
    Tests for the user profile endpoint: /me/.
    """
    def test_get_user_profile_success(self):
        """
        Ensure an authenticated user can retrieve their own profile.
        """
        self.authenticate_client(self.user)
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertIn('alerts', response.data)

    def test_get_user_profile_fails_if_unauthenticated(self):
        """
        Ensure an unauthenticated user cannot access the profile endpoint.
        """
        self.unauthenticate_client()
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
