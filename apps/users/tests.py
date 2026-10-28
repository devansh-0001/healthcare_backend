from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.users.models import User


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('auth-register')
        self.login_url = reverse('auth-login')
        self.refresh_url = reverse('auth-token-refresh')

        self.user_data = {
            'name': 'Devansh',
            'email': 'dev@example.com',
            'password': 'StrongPass#123'
        }

    def test_register_user_success(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Devansh')
        self.assertEqual(response.data['email'], 'dev@example.com')
        self.assertNotIn('password', response.data)
        self.assertTrue(User.objects.filter(email='dev@example.com').exists())

    def test_register_duplicate_email_conflict(self):
        # First registration
        self.client.post(self.register_url, self.user_data, format='json')
        # Duplicate registration with different case
        duplicate_data = {
            'name': 'Devansh Duplicate',
            'email': 'DEV@example.com',
            'password': 'StrongPass#123'
        }
        response = self.client.post(self.register_url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['code'], 'conflict')

    def test_register_short_password_validation_error(self):
        data = {
            'name': 'Devansh',
            'email': 'short@example.com',
            'password': 'short'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'validation_error')

    def test_login_success(self):
        # Create user
        self.client.post(self.register_url, self.user_data, format='json')

        login_data = {
            'email': 'dev@example.com',
            'password': 'StrongPass#123'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'dev@example.com')
        self.assertEqual(response.data['user']['name'], 'Devansh')

    def test_login_invalid_credentials(self):
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'WrongPassword123'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'validation_error')

    def test_token_refresh(self):
        # Register and login to get refresh token
        self.client.post(self.register_url, self.user_data, format='json')
        login_res = self.client.post(self.login_url, {
            'email': 'dev@example.com',
            'password': 'StrongPass#123'
        }, format='json')
        refresh_token = login_res.data['refresh']

        response = self.client.post(self.refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@synora.com',
            name='Admin User',
            password='AdminPass#123'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(str(admin), 'Admin User <admin@synora.com>')
