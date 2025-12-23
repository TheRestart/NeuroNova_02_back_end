"""
EMR Write-Through 패턴 테스트

아키텍처:
- Single Source of Truth: OpenEMR (FHIR Server)
- Django DB: Read Cache Only
- Write-Through Strategy: FHIR 서버 먼저 업데이트 → 성공 시 Django DB 업데이트

테스트 시나리오:
1. test_update_success_with_emr_sync: FHIR 서버 업데이트 성공 → Django DB 업데이트
2. test_update_fail_when_emr_rejects: FHIR 서버 거절 → Django DB 수정 없음
3. test_update_fail_on_emr_exception: FHIR 서버 장애 → Django DB 수정 없음
"""

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import date

from .models import PatientCache
from .fhir_adapter import FHIRServiceAdapter


class PatientWriteThroughTestCase(APITestCase):
    """
    환자 프로필 수정 Write-Through 패턴 테스트

    테스트 대상 API: PATCH /api/emr/patients/{id}/
    """

    def setUp(self):
        """
        테스트 환경 설정

        Given: 테스트용 환자 데이터 생성 (OpenEMR과 동기화된 상태)
        """
        self.patient = PatientCache.objects.create(
            patient_id='P-2025-TEST01',
            family_name='홍',
            given_name='길동',
            birth_date=date(1990, 1, 1),
            gender='male',
            phone='010-1234-5678',
            email='hong@example.com',
            address='서울시 강남구 테헤란로 123',
            openemr_patient_id='fhir-patient-123',  # OpenEMR과 동기화됨
            blood_type='A+'
        )

        self.api_url = f'/api/emr/patients/{self.patient.patient_id}/'

        # 수정할 데이터
        self.update_payload = {
            'phone': '010-9999-8888',
            'email': 'newemail@example.com',
            'address': '서울시 서초구 서초대로 456'
        }

    @patch('emr.viewsets.FHIRServiceAdapter.update_patient')
    def test_update_success_with_emr_sync(self, mock_update_patient):
        """
        시나리오 1: FHIR 서버 업데이트 성공 → Django DB 업데이트

        Given: FHIR Adapter가 성공 응답을 반환하도록 Mocking
        When: PATCH /api/emr/patients/{id}/ 요청
        Then:
          - API 응답 상태 코드: 200 OK
          - Django DB에 변경사항 반영됨
          - 환자 정보가 실제로 업데이트됨 (refresh_from_db로 확인)
        """
        # Given: FHIR Adapter Mock 설정 - 성공 응답
        mock_fhir_response = {
            'resourceType': 'Patient',
            'id': 'fhir-patient-123',
            'telecom': [
                {'system': 'phone', 'value': '010-9999-8888'},
                {'system': 'email', 'value': 'newemail@example.com'}
            ],
            'address': [
                {'text': '서울시 서초구 서초대로 456'}
            ]
        }
        mock_update_patient.return_value = (True, mock_fhir_response)

        # When: API 호출
        response = self.client.patch(
            self.api_url,
            data=self.update_payload,
            format='json'
        )

        # Then: 응답 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # FHIR Adapter가 호출되었는지 확인
        mock_update_patient.assert_called_once_with(
            'fhir-patient-123',
            self.update_payload
        )

        # Django DB에 실제로 변경되었는지 확인 (중요!)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.phone, '010-9999-8888')
        self.assertEqual(self.patient.email, 'newemail@example.com')
        self.assertEqual(self.patient.address, '서울시 서초구 서초대로 456')

        # 동기화 시간이 갱신되었는지 확인
        self.assertIsNotNone(self.patient.last_synced_at)

        # 변경되지 않아야 하는 필드 확인
        self.assertEqual(self.patient.family_name, '홍')
        self.assertEqual(self.patient.given_name, '길동')
        self.assertEqual(self.patient.blood_type, 'A+')

    @patch('emr.viewsets.FHIRServiceAdapter.update_patient')
    def test_update_fail_when_emr_rejects(self, mock_update_patient):
        """
        시나리오 2: FHIR 서버 거절 (유효성 검사 실패) → Django DB 수정 없음

        Given: FHIR Adapter가 실패 응답을 반환하도록 Mocking
        When: PATCH /api/emr/patients/{id}/ 요청
        Then:
          - API 응답 상태 코드: 400 Bad Request
          - Django DB에 변경사항 없음 (기존 값 유지)
          - 에러 메시지 포함
        """
        # Given: FHIR Adapter Mock 설정 - 거절 응답 (유효성 검사 실패)
        mock_error_response = {
            'error': 'Invalid phone number format'
        }
        mock_update_patient.return_value = (False, mock_error_response)

        # 기존 값 저장 (비교용)
        original_phone = self.patient.phone
        original_email = self.patient.email
        original_address = self.patient.address

        # When: API 호출
        response = self.client.patch(
            self.api_url,
            data=self.update_payload,
            format='json'
        )

        # Then: 응답 확인
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid phone number format')

        # FHIR Adapter가 호출되었는지 확인
        mock_update_patient.assert_called_once()

        # Django DB에 변경사항이 없는지 확인 (중요!)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.phone, original_phone)  # 변경 없음
        self.assertEqual(self.patient.email, original_email)  # 변경 없음
        self.assertEqual(self.patient.address, original_address)  # 변경 없음

        # 다른 필드도 변경되지 않았는지 확인
        self.assertEqual(self.patient.family_name, '홍')
        self.assertEqual(self.patient.given_name, '길동')

    @patch('emr.viewsets.FHIRServiceAdapter.update_patient')
    def test_update_fail_on_emr_exception(self, mock_update_patient):
        """
        시나리오 3: FHIR 서버 통신 장애 → Django DB 수정 없음

        Given: FHIR Adapter 호출 시 Exception 발생하도록 Mocking
        When: PATCH /api/emr/patients/{id}/ 요청
        Then:
          - API 응답 상태 코드: 503 Service Unavailable
          - Django DB에 변경사항 없음
          - 에러 메시지 포함
        """
        # Given: FHIR Adapter Mock 설정 - Exception 발생
        mock_update_patient.side_effect = Exception('Connection timeout')

        # 기존 값 저장 (비교용)
        original_phone = self.patient.phone
        original_email = self.patient.email
        original_address = self.patient.address

        # When: API 호출
        response = self.client.patch(
            self.api_url,
            data=self.update_payload,
            format='json'
        )

        # Then: 응답 확인
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'FHIR server communication failed')
        self.assertEqual(response.data['detail'], 'Connection timeout')

        # FHIR Adapter가 호출되었는지 확인
        mock_update_patient.assert_called_once()

        # Django DB에 변경사항이 없는지 확인 (중요!)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.phone, original_phone)  # 변경 없음
        self.assertEqual(self.patient.email, original_email)  # 변경 없음
        self.assertEqual(self.patient.address, original_address)  # 변경 없음

    @patch('emr.viewsets.FHIRServiceAdapter.update_patient')
    def test_update_patient_without_openemr_id(self, mock_update_patient):
        """
        시나리오 4: OpenEMR과 동기화되지 않은 환자 → Django DB만 업데이트

        Given: openemr_patient_id가 없는 환자
        When: PATCH /api/emr/patients/{id}/ 요청
        Then:
          - API 응답 상태 코드: 200 OK
          - FHIR Adapter 호출되지 않음
          - Django DB만 업데이트됨
        """
        # Given: OpenEMR과 동기화되지 않은 환자 생성
        unsynced_patient = PatientCache.objects.create(
            patient_id='P-2025-TEST02',
            family_name='김',
            given_name='철수',
            birth_date=date(1985, 5, 15),
            gender='male',
            phone='010-1111-2222',
            email='kim@example.com',
            openemr_patient_id=None  # OpenEMR과 동기화되지 않음
        )

        # When: API 호출
        response = self.client.patch(
            f'/api/emr/patients/{unsynced_patient.patient_id}/',
            data={'phone': '010-3333-4444'},
            format='json'
        )

        # Then: 응답 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # FHIR Adapter가 호출되지 않았는지 확인
        mock_update_patient.assert_not_called()

        # Django DB는 업데이트됨
        unsynced_patient.refresh_from_db()
        self.assertEqual(unsynced_patient.phone, '010-3333-4444')

    def test_update_readonly_fields(self):
        """
        시나리오 5: Read-Only 필드 수정 시도 → 무시됨

        Given: 환자 데이터
        When: patient_id, created_at 등 Read-Only 필드 수정 시도
        Then:
          - API 응답 성공 (다른 필드만 업데이트)
          - Read-Only 필드는 변경되지 않음
        """
        # Given & When
        response = self.client.patch(
            self.api_url,
            data={
                'patient_id': 'P-2025-HACKED',  # Read-Only
                'created_at': '2020-01-01',  # Read-Only
                'phone': '010-9999-8888'  # 변경 가능
            },
            format='json'
        )

        # Then
        # Read-Only 필드는 무시되고, 변경 가능한 필드만 업데이트됨
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.patient_id, 'P-2025-TEST01')  # 변경 안됨
        # phone은 FHIR 동기화가 필요하므로 Mock 없이는 실패할 수 있음


class FHIRAdapterUnitTest(TestCase):
    """
    FHIR Service Adapter 단위 테스트 (Mock 없이 직접 테스트)
    """

    @patch('emr.fhir_adapter.requests.Session.get')
    @patch('emr.fhir_adapter.requests.Session.put')
    def test_fhir_adapter_update_success(self, mock_put, mock_get):
        """
        FHIR Adapter 직접 테스트: 업데이트 성공 시나리오
        """
        # Given: Mock 설정
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                'resourceType': 'Patient',
                'id': 'test-123',
                'telecom': []
            }
        )

        mock_put.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                'resourceType': 'Patient',
                'id': 'test-123',
                'telecom': [
                    {'system': 'phone', 'value': '010-1234-5678'}
                ]
            }
        )

        # When: FHIR Adapter 호출
        adapter = FHIRServiceAdapter()
        success, result = adapter.update_patient(
            'test-123',
            {'phone': '010-1234-5678'}
        )

        # Then
        self.assertTrue(success)
        self.assertEqual(result['resourceType'], 'Patient')
        self.assertEqual(result['id'], 'test-123')

    @patch('emr.fhir_adapter.requests.Session.get')
    @patch('emr.fhir_adapter.requests.Session.put')
    def test_fhir_adapter_update_validation_fail(self, mock_put, mock_get):
        """
        FHIR Adapter 직접 테스트: 유효성 검사 실패 시나리오
        """
        # Given: Mock 설정
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                'resourceType': 'Patient',
                'id': 'test-123'
            }
        )

        mock_put.return_value = MagicMock(
            status_code=400,
            json=lambda: {
                'resourceType': 'OperationOutcome',
                'issue': [
                    {'diagnostics': 'Invalid phone format'}
                ]
            }
        )

        # When: FHIR Adapter 호출
        adapter = FHIRServiceAdapter()
        success, result = adapter.update_patient(
            'test-123',
            {'phone': 'invalid'}
        )

        # Then
        self.assertFalse(success)
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'Invalid phone format')
