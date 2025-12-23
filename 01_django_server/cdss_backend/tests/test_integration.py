from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase
from django.urls import reverse
from acct.models import User

class SecurityIntegrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.ris_url = '/api/ris/studies/'  # Adjust if actual URL differs
        
        # Create a doctor user
        self.doctor = User.objects.create_user(
            username='dr_house',
            email='house@hospital.com',
            password='Password123!',
            role='doctor',
            full_name='Gregory House'
        )

    def test_ris_endpoint_security(self):
        """RIS 엔드포인트 보안 테스트"""
        
        # 1. Unauthenticated Request
        response = self.client.get(self.ris_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                         f"Expected 401 for unauthenticated access, got {response.status_code}")

        # 2. Authenticated Request
        self.client.force_authenticate(user=self.doctor)
        response = self.client.get(self.ris_url)
        
        # We expect 200 OK (empty list) or some valid response, NOT 401/403
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)
