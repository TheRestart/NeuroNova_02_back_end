"""
OpenEMR 연동 및 Write-Through 패턴 유닛 테스트

이 테스트 모듈은 다음 항목을 검증합니다:
1. OpenEMRClient (HTTP 연동)
2. EMR Views (Basic Endpoints)
3. EMR CRUD (Service Layer Mocking)
4. Write-Through Caching Pattern (New)

주의: IntegrationTest는 실제 서버 부재 시 스킵 처리함.
"""

from django.test import TestCase, Client
from unittest.mock import patch, Mock, MagicMock
import json
import requests
import unittest
from .openemr_client import OpenEMRClient
from .models import PatientCache, Encounter, Order, OrderItem
from django.utils import timezone

class OpenEMRClientTestCase(TestCase):
    """OpenEMRClient 클래스 유닛 테스트"""

    def setUp(self):
        self.client = OpenEMRClient(base_url="http://localhost:80")

    @patch('requests.Session.get')
    def test_health_check_success(self, mock_get):
        """서버 상태 확인 성공 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = self.client.health_check()
        self.assertEqual(result["status"], "healthy")

    @patch('requests.Session.get')
    def test_health_check_failure(self, mock_get):
        """서버 상태 확인 실패 테스트"""
        mock_get.side_effect = requests.RequestException("Connection failed")
        result = self.client.health_check()
        self.assertEqual(result["status"], "error")

    @patch('requests.Session.post')
    def test_authenticate_success(self, mock_post):
        """인증 성공 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response

        result = self.client.authenticate("admin", "pass")
        self.assertTrue(result["success"])

    @patch('requests.Session.get')
    def test_get_patient_by_id(self, mock_get):
        """특정 환자 조회 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resourceType": "Patient",
            "id": "1",
            "name": [{"given": ["John"], "family": "Doe"}]
        }
        mock_get.return_value = mock_response

        result = self.client.get_patient("1")
        self.assertEqual(result["id"], "1")


class EMRViewsTestCase(TestCase):
    """EMR Django views API 엔드포인트 테스트"""

    def setUp(self):
        self.client = Client()

    @patch('emr.views.client')
    def test_health_check_endpoint(self, mock_client):
        """Health check 엔드포인트 테스트"""
        mock_client.health_check.return_value = {"status": "healthy", "status_code": 200}
        response = self.client.get('/api/emr/health/')
        self.assertEqual(response.status_code, 200)

    @patch('emr.views.client')
    def test_list_patients_endpoint(self, mock_client):
        """환자 목록 조회 엔드포인트 테스트"""
        mock_client.get_patients.return_value = []
        response = self.client.get('/api/emr/patients/?limit=10')
        self.assertEqual(response.status_code, 200)


@unittest.skip("실제 OpenEMR 서버가 없어 localhost 연결 에러 발생하므로 스킵")
class EMRIntegrationTestCase(TestCase):
    """OpenEMR 통합 테스트 (실제 서버 필요)"""
    pass


class EMRCRUDTestCase(TestCase):
    """
    CRUD 기능 (Patient, Order, OrderItem) 유닛 테스트
    - OpenEMRPatientRepository Mocking 필수 (DB 연결 에러 방지)
    """
    
    def setUp(self):
        self.client = Client()
        self.patient_data = {
            "family_name": "Test",
            "given_name": "User",
            "birth_date": "1990-01-01",
            "gender": "male",
            "phone": "010-1234-5678",
            "email": "test@example.com"
        }

    @patch('emr.services.OpenEMRPatientRepository.create_patient_in_openemr')
    def test_create_patient(self, mock_create_openemr):
        """환자 생성 테스트"""
        mock_create_openemr.return_value = 12345
        response = self.client.post('/api/emr/patients/', data=self.patient_data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(PatientCache.objects.filter(family_name="Test").exists())

    @patch('emr.services.OpenEMRPatientRepository.create_patient_in_openemr')
    def test_create_order_with_items(self, mock_create_openemr):
        """처방 생성 및 항목 자동 생성 테스트"""
        mock_create_openemr.return_value = 12345
        
        # 1. 환자 생성
        p_res = self.client.post('/api/emr/patients/', data=self.patient_data, content_type='application/json')
        patient_id = p_res.json()['patient_id']

        # 2. 처방 생성
        order_data = {
            "patient": patient_id,
            "order_type": "medication",
            "urgency": "routine",
            "ordered_by": "doctor_1",  # [Fix] 필수 필드 추가
            "order_items": [
                {
                    "drug_code": "D001",
                    "drug_name": "Tylenol",
                    "dosage": "500mg",
                    "frequency": "BID",
                    "duration": "3 days"
                }
            ]
        }
        response = self.client.post('/api/emr/orders/', data=order_data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
        # 3. 항목 생성 확인
        order_id = response.json()['order_id']
        self.assertEqual(OrderItem.objects.filter(item_id__startswith=f"OI-{order_id}").count(), 1)


class WriteThroughTestCase(TestCase):
    """
    [아키텍처 규칙 검증] Write-Through 패턴 테스트
    
    규칙:
    1. Django DB는 Read-Only Cache 역할 (Single Source of Truth는 OpenEMR)
    2. 수정 시 FHIR 서버에 먼저 요청 (선행 업데이트)
    3. FHIR 성공 -> Django DB 업데이트
    4. FHIR 실패 -> Django DB 업데이트 거부
    """

    def setUp(self):
        """Given: OpenEMR과 동기화된(pid 존재) 환자 데이터 준비"""
        self.client = Client()
        self.patient = PatientCache.objects.create(
            patient_id="P-2025-000001",
            family_name="Target",
            given_name="Patient",
            birth_date="2000-01-01",
            gender="male",
            phone="010-0000-0000",
            email="before@example.com",
            openemr_patient_id="100"  # 중요: 동기화된 상태
        )
        self.url = f'/api/emr/patients/{self.patient.patient_id}/'

    @patch('emr.viewsets.FHIRServiceAdapter')
    def test_update_success_with_emr_sync(self, MockAdapter):
        """
        Scenario 1: FHIR 서버 업데이트 성공 시 Django DB도 업데이트되어야 함
        """
        # Given: Adapter Mocking (성공 응답)
        mock_instance = MockAdapter.return_value
        mock_instance.update_patient.return_value = (True, {"resourceType": "Patient"})
        
        update_data = {"email": "updated@example.com"}

        # When: API 호출 (PATCH)
        response = self.client.patch(
            self.url,
            data=update_data,
            content_type='application/json'
        )

        # Then: 200 OK + DB 업데이트 확인
        self.assertEqual(response.status_code, 200)
        
        self.patient.refresh_from_db()  # DB 새로고침
        self.assertEqual(self.patient.email, "updated@example.com")
        
        # Adapter 호출 검증
        mock_instance.update_patient.assert_called_once()

    @patch('emr.viewsets.FHIRServiceAdapter')
    def test_update_fail_when_emr_rejects(self, MockAdapter):
        """
        Scenario 2: FHIR 서버 거절(400) 시 Django DB 업데이트는 롤백(유지)되어야 함
        """
        # Given: Adapter Mocking (실패/거절 응답)
        mock_instance = MockAdapter.return_value
        mock_instance.update_patient.return_value = (False, {"error": "Invalid email format"})
        
        update_data = {"email": "invalid-email"}

        # When: API 호출
        response = self.client.patch(
            self.url,
            data=update_data,
            content_type='application/json'
        )

        # Then: 400 Bad Request + DB 변경 없음 확인
        self.assertEqual(response.status_code, 400)
        
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.email, "before@example.com")  # 변경되지 않아야 함

    @patch('emr.viewsets.FHIRServiceAdapter')
    def test_update_fail_on_emr_exception(self, MockAdapter):
        """
        Scenario 3: FHIR 서버 장애/예외 발생 시 503 에러 반환 및 DB 유지
        """
        # Given: Adapter Mocking (예외 발생)
        mock_instance = MockAdapter.return_value
        mock_instance.update_patient.side_effect = Exception("FHIR Server Down")
        
        update_data = {"email": "updated@example.com"}

        # When: API 호출
        response = self.client.patch(
            self.url,
            data=update_data,
            content_type='application/json'
        )

        # Then: 503 Service Unavailable + DB 변경 없음 확인
        self.assertEqual(response.status_code, 503)
        
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.email, "before@example.com")
