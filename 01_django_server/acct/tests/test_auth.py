from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from acct.models import User

class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/acct/users/register/'
        self.login_url = '/api/acct/login/'
        
        # 7 roles to test
        self.roles = [
            'admin', 'doctor', 'rib', 'lab', 
            'nurse', 'patient', 'external'
        ]

    def test_registration_all_roles(self):
        """7개 역할별 회원가입 테스트"""
        for role in self.roles:
            data = {
                'username': f'test_{role}',
                'email': f'{role}@example.com',
                'password': 'StrongPassword123!',
                'password_confirm': 'StrongPassword123!',
                'role': role,
                'full_name': f'Test {role.capitalize()}'
            }
            response = self.client.post(self.register_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, 
                             f"Failed to register role: {role}. Response: {response.data}")
            
            # Verify DB content
            user = User.objects.get(username=data['username'])
            self.assertEqual(user.role, role)
            self.assertTrue(user.check_password(data['password']))

    def test_login_and_token_generation(self):
        """로그인 및 JWT 토큰 발급 테스트"""
        # Create a user first
        user = User.objects.create_user(
            username='auth_test',
            email='auth@example.com',
            password='Password123!',
            role='doctor',
            full_name='Auth Tester'
        )
        
        data = {
            'username': 'auth_test',
            'password': 'Password123!'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify token structure
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], user.username)

    def test_login_invalid_credentials(self):
        """잘못된 비밀번호 로그인 실패 테스트"""
        User.objects.create_user(
            username='fail_test',
            email='fail@example.com',
            password='CorrectPassword',
            role='patient',
            full_name='Fail Tester'
        )
        
        data = {
            'username': 'fail_test',
            'password': 'WrongPassword'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
