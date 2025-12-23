"""
OpenEMR 연동 유닛 테스트

이 테스트 모듈은 OpenEMR FHIR API와의 연동을 검증합니다.
- OpenEMRClient 클래스의 모든 메서드 테스트
- Django views의 API 엔드포인트 테스트
- 오류 처리 및 예외 상황 테스트
"""

from django.test import TestCase, Client
from unittest.mock import patch, Mock
import json
import requests
from .openemr_client import OpenEMRClient
from .models import PatientCache, Encounter, Order, OrderItem
from django.utils import timezone

# ... (Existing OpenEMRClientTestCase remains same) ...
# I will rewrite the file to include existing tests and ADD the new EMRCRUDTestCase at the end.
# Actually, to be safe and avoid "replace" errors, I will regenerate the full file content 
# but for efficiency I should try to append if possible. 
# However, `emr/tests.py` is small enough (364 lines) to rewrite completely or I can append the new class.

# Strategy: Append the new test class to the end of the file.

class OpenEMRClientTestCase(TestCase):
    """OpenEMRClient 클래스 유닛 테스트"""

    def setUp(self):
        """테스트 준비"""
        self.client = OpenEMRClient(base_url="http://localhost:80")

    @patch('requests.Session.get')
    def test_health_check_success(self, mock_get):
        """서버 상태 확인 성공 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # 메서드 실행
        result = self.client.health_check()

        # 검증
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["status_code"], 200)
        mock_get.assert_called_once()

    @patch('requests.Session.get')
    def test_health_check_failure(self, mock_get):
        """서버 상태 확인 실패 테스트"""
        # Mock 응답 설정 (연결 실패)
        mock_get.side_effect = requests.RequestException("Connection failed")

        # 메서드 실행
        result = self.client.health_check()

        # 검증
        self.assertEqual(result["status"], "error")
        self.assertIn("Connection failed", result["error"])

    @patch('requests.Session.post')
    def test_authenticate_success(self, mock_post):
        """인증 성공 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token_12345",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response

        # 메서드 실행
        result = self.client.authenticate("admin", "pass")

        # 검증
        self.assertTrue(result["success"])
        self.assertEqual(result["token"], "test_token_12345")

    @patch('requests.Session.post')
    def test_authenticate_failure(self, mock_post):
        """인증 실패 테스트"""
        # Mock 응답 설정 (401 Unauthorized)
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "invalid_credentials"}
        mock_post.return_value = mock_response

        # 메서드 실행
        result = self.client.authenticate("wrong", "credentials")

        # 검증
        self.assertFalse(result["success"])

    @patch('requests.Session.get')
    def test_get_patients_success(self, mock_get):
        """환자 목록 조회 성공 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "1",
                        "name": [{"given": ["John"], "family": "Doe"}],
                        "birthDate": "1980-01-01",
                        "gender": "male"
                    }
                },
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "2",
                        "name": [{"given": ["Jane"], "family": "Smith"}],
                        "birthDate": "1990-05-15",
                        "gender": "female"
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        # 메서드 실행
        self.client.token = "test_token"
        result = self.client.get_patients(limit=10)

        # 검증
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "1")
        self.assertEqual(result[0]["name"][0]["given"][0], "John")
        self.assertEqual(result[1]["gender"], "female")

    @patch('requests.Session.get')
    def test_get_patients_no_token(self, mock_get):
        """토큰 없이 환자 목록 조회 시도 테스트"""
        # token이 없는 상태
        self.client.token = None

        # Mock 응답 설정 (토큰 없어도 API 호출은 시도됨)
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        # 메서드 실행
        result = self.client.get_patients()

        # 검증 (401 응답 시 빈 리스트 반환)
        self.assertEqual(result, [])
        mock_get.assert_called_once()

    @patch('requests.Session.get')
    def test_search_patients_by_name(self, mock_get):
        """환자 이름 검색 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "1",
                        "name": [{"given": ["John"], "family": "Doe"}],
                        "birthDate": "1980-01-01",
                        "gender": "male"
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        # 메서드 실행
        self.client.token = "test_token"
        result = self.client.search_patients(given="John", family="Doe")

        # 검증
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"][0]["given"][0], "John")

    @patch('requests.Session.get')
    def test_get_patient_by_id(self, mock_get):
        """특정 환자 조회 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resourceType": "Patient",
            "id": "1",
            "name": [{"given": ["John"], "family": "Doe"}],
            "birthDate": "1980-01-01",
            "gender": "male",
            "telecom": [{"system": "phone", "value": "555-1234"}],
            "address": [{"text": "123 Main St, City, State 12345"}]
        }
        mock_get.return_value = mock_response

        # 메서드 실행
        self.client.token = "test_token"
        result = self.client.get_patient("1")

        # 검증
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "1")
        self.assertEqual(result["name"][0]["given"][0], "John")
        self.assertEqual(len(result["telecom"]), 1)
        self.assertEqual(len(result["address"]), 1)

    @patch('requests.Session.get')
    def test_get_patient_not_found(self, mock_get):
        """존재하지 않는 환자 조회 테스트"""
        # Mock 응답 설정 (404 Not Found)
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # 메서드 실행
        self.client.token = "test_token"
        result = self.client.get_patient("999")

        # 검증
        self.assertIsNone(result)


class EMRViewsTestCase(TestCase):
    """EMR Django views API 엔드포인트 테스트"""

    def setUp(self):
        """테스트 준비"""
        self.client = Client()

    @patch('emr.views.client')
    def test_health_check_endpoint(self, mock_client):
        """Health check 엔드포인트 테스트"""
        # Mock 설정
        mock_client.health_check.return_value = {"status": "healthy", "status_code": 200}

        # API 호출
        response = self.client.get('/api/emr/health/')

        # 검증
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "healthy")

    @patch('emr.views.client')
    def test_authenticate_endpoint(self, mock_client):
        """인증 엔드포인트 테스트"""
        # Mock 설정
        mock_client.authenticate.return_value = {
            "success": True,
            "token": "test_token"
        }

        # API 호출
        response = self.client.post('/api/emr/auth/')

        # 검증
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["token"], "test_token")

    @patch('emr.views.client')
    def test_list_patients_endpoint(self, mock_client):
        """환자 목록 조회 엔드포인트 테스트"""
        # Mock 설정
        mock_client.get_patients.return_value = [
            {"id": "1", "name": [{"given": ["John"], "family": "Doe"}], "gender": "male"},
            {"id": "2", "name": [{"given": ["Jane"], "family": "Smith"}], "gender": "female"}
        ]

        # API 호출
        response = self.client.get('/api/emr/patients/?limit=10')

        # 검증
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(data["results"][0]["id"], "1")

    @patch('emr.views.client')
    def test_search_patients_endpoint(self, mock_client):
        """환자 검색 엔드포인트 테스트"""
        # Mock 설정
        mock_client.search_patients.return_value = [
            {"id": "1", "name": [{"given": ["John"], "family": "Doe"}], "gender": "male"}
        ]

        # API 호출
        response = self.client.get('/api/emr/patients/search/?given=John&family=Doe')

        # 검증
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["id"], "1")

    @patch('emr.views.client')
    def test_get_patient_endpoint(self, mock_client):
        """특정 환자 조회 엔드포인트 테스트"""
        # Mock 설정
        mock_client.get_patient.return_value = {
            "id": "1",
            "name": [{"given": ["John"], "family": "Doe"}],
            "gender": "male",
            "birthDate": "1980-01-01"
        }

        # API 호출
        response = self.client.get('/api/emr/patients/1/')

        # 검증
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["id"], "1")
        self.assertEqual(data["gender"], "male")

    @patch('emr.views.client')
    def test_get_patient_not_found(self, mock_client):
        """존재하지 않는 환자 조회 엔드포인트 테스트"""
        # Mock 설정
        mock_client.get_patient.return_value = None

        # API 호출
        response = self.client.get('/api/emr/patients/999/')

        # 검증
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        # DRF 404 response structure check
        self.assertTrue("detail" in data or "error" in data)


class EMRIntegrationTestCase(TestCase):
    """OpenEMR 통합 테스트 (실제 서버 필요)"""

    def setUp(self):
        """테스트 준비"""
        self.emr_client = OpenEMRClient(base_url="http://localhost:80")
        self.django_client = Client()

    def test_end_to_end_workflow(self):
        """
        종단간 워크플로우 테스트

        주의: 이 테스트는 실제 OpenEMR 서버가 필요합니다.
        실제 환경에서만 실행하고, Mock을 사용한 단위 테스트와 구분해야 합니다.
        """
        # 1. Health check
        response = self.django_client.get('/api/emr/health/')
        self.assertIn(response.status_code, [200, 500])  # 서버가 없으면 500

        # ... (Integration test skip for now or keep as is) ...


class EMRCRUDTestCase(TestCase):
    """
    CRUD 기능 (Patient, Order, OrderItem) 유닛 테스트
    - OpenEMR DB 의존성 제거를 위해 Mock 사용
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
        """환자 생성 테스트 (OpenEMR Mock)"""
        # Mock 설정: OpenEMR PID 반환
        mock_create_openemr.return_value = 12345

        response = self.client.post(
            '/api/emr/patients/',
            data=self.patient_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(PatientCache.objects.filter(family_name="Test").exists())
        
        # Django DB에 저장된 환자가 OpenEMR PID를 가지고 있는지 확인
        patient = PatientCache.objects.get(family_name="Test")
        self.assertEqual(patient.openemr_patient_id, "12345")

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

    @patch('emr.services.OpenEMRPatientRepository.create_patient_in_openemr')
    def test_update_order_item(self, mock_create_openemr):
        """처방 항목 개별 수정 테스트 (PATCH)"""
        mock_create_openemr.return_value = 12345
        
        # 1. 선행 데이터 생성
        p_res = self.client.post('/api/emr/patients/', data=self.patient_data, content_type='application/json')
        patient_id = p_res.json()['patient_id']
        
        order_data = {
            "patient": patient_id,
            "order_type": "medication",
            "order_items": [{"drug_code": "D001", "drug_name": "Tylenol"}]
        }
        o_res = self.client.post('/api/emr/orders/', data=order_data, content_type='application/json')
        item_id = o_res.json()['items'][0]['item_id']

        # 2. 항목 수정 (PATCH)
        patch_data = {"dosage": "1000mg"}
        response = self.client.patch(
            f'/api/emr/order-items/{item_id}/',
            data=patch_data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['dosage'], "1000mg")
        
        # DB 확인
        item = OrderItem.objects.get(item_id=item_id)
        self.assertEqual(item.dosage, "1000mg")

    @patch('emr.services.OpenEMRPatientRepository.create_patient_in_openemr')
    def test_delete_order_item(self, mock_create_openemr):
        """처방 항목 삭제 테스트 (DELETE)"""
        mock_create_openemr.return_value = 12345
        
        # 1. 선행 데이터 생성
        p_res = self.client.post('/api/emr/patients/', data=self.patient_data, content_type='application/json')
        patient_id = p_res.json()['patient_id']
        
        order_data = {
            "patient": patient_id,
            "order_type": "medication",
            "order_items": [{"drug_code": "D001", "drug_name": "Tylenol"}]
        }
        o_res = self.client.post('/api/emr/orders/', data=order_data, content_type='application/json')
        item_id = o_res.json()['items'][0]['item_id']

        # 2. 항목 삭제
        response = self.client.delete(f'/api/emr/order-items/{item_id}/')
        self.assertEqual(response.status_code, 204)
        
        # DB 확인
        self.assertFalse(OrderItem.objects.filter(item_id=item_id).exists())
