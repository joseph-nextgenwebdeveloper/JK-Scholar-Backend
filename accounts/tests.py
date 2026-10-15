"""
Tests for user authentication, registration, login, logout, and token handling.
"""

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.me_url = reverse('accounts:current_user')

        self.user_data = {
            'username': 'student1',
            'email': 'student1@example.com',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
            'first_name': 'John',
            'last_name': 'Doe'
        }

    def test_user_registration_success(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'student1@example.com')
        self.assertTrue(User.objects.filter(username='student1').exists())

    def test_registration_password_mismatch(self):
        invalid_data = self.user_data.copy()
        invalid_data['password_confirm'] = 'DifferentPassword123!'
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_registration_duplicate_email(self):
        self.client.post(self.register_url, self.user_data, format='json')
        duplicate_data = self.user_data.copy()
        duplicate_data['username'] = 'anotheruser'
        response = self.client.post(self.register_url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        login_payload = {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_user_login_invalid_credentials(self):
        login_payload = {
            'username': 'nonexistent',
            'password': 'WrongPassword123!'
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_api_access(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_user_profile_authenticated(self):
        user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], user.username)
        self.assertEqual(response.data['email'], user.email)

    def test_user_logout(self):
        user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        login_res = self.client.post(self.login_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }, format='json')
        refresh_token = login_res.data['refresh']

        self.client.force_authenticate(user=user)
        logout_res = self.client.post(self.logout_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)


class SessionAndRegisterHardeningTests(APITestCase):
    def test_register_is_case_insensitive_on_email_and_username(self):
        url = reverse('accounts:register')
        base = {'username': 'Student1', 'email': 'Student1@Example.com',
                'password': 'SecurePassword123!', 'password_confirm': 'SecurePassword123!'}
        self.assertEqual(self.client.post(url, base, format='json').status_code, 201)
        again = dict(base, username='student1', email='other@example.com')
        self.assertEqual(self.client.post(url, again, format='json').status_code, 400)
        again = dict(base, username='someone', email='STUDENT1@example.com')
        self.assertEqual(self.client.post(url, again, format='json').status_code, 400)

    def test_refresh_rotates_and_new_refresh_works(self):
        User.objects.create_user(username='a', email='a@example.com', password='SecurePassword123!')
        r = self.client.post(reverse('accounts:login'),
                             {'username': 'a', 'password': 'SecurePassword123!'}, format='json')
        refresh = r.data['refresh']
        url = reverse('accounts:token_refresh')
        r1 = self.client.post(url, {'refresh': refresh}, format='json')
        self.assertEqual(r1.status_code, 200)
        self.assertIn('refresh', r1.data)               # the client must keep this one
        self.assertEqual(self.client.post(url, {'refresh': refresh}, format='json').status_code, 401)
        self.assertEqual(self.client.post(url, {'refresh': r1.data['refresh']}, format='json').status_code, 200)
