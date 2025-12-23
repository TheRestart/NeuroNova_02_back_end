"""
FHIR Service Adapter

OpenEMR (FHIR Server)과의 통신을 담당하는 어댑터
Write-Through 전략을 사용하여 데이터 일관성 보장
"""
import logging
from typing import Dict, Tuple, Optional
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class FHIRServiceAdapter:
    """
    FHIR 서버와의 통신을 담당하는 어댑터 클래스

    Single Source of Truth: OpenEMR (FHIR Server)
    Django DB: Read Cache Only

    데이터 수정 흐름 (Write-Through):
    1. FHIR 서버에 수정 요청
    2. 성공하면 Django DB 업데이트
    3. 실패하면 Django DB 수정 없이 에러 반환
    """

    def __init__(self, base_url: str = None):
        """
        Args:
            base_url: OpenEMR FHIR API URL (기본값: settings.OPENEMR_FHIR_URL)
        """
        self.base_url = base_url or getattr(
            settings,
            'FHIR_SERVER_URL',
            'http://localhost:8080/fhir'
        )
        self.session = requests.Session()
        self.token = None

    def update_patient(self, patient_id: str, update_data: Dict) -> Tuple[bool, Dict]:
        """
        환자 정보를 FHIR 서버에 업데이트

        Args:
            patient_id: OpenEMR Patient ID (FHIR Resource ID)
            update_data: 업데이트할 데이터 딕셔너리
                {
                    'phone': '010-1234-5678',
                    'email': 'patient@example.com',
                    'address': '서울시 강남구...'
                }

        Returns:
            Tuple[bool, Dict]:
                - (True, {업데이트된 FHIR Patient 리소스}): 성공
                - (False, {error: "에러 메시지"}): 실패 (유효성 검사 등)

        Raises:
            Exception: 네트워크 오류, 서버 장애 등
        """
        try:
            # FHIR Patient 리소스 조회
            patient_resource = self._get_patient_resource(patient_id)
            if not patient_resource:
                return False, {"error": f"Patient {patient_id} not found in FHIR server"}

            # FHIR 리소스 업데이트
            updated_resource = self._merge_patient_data(patient_resource, update_data)

            # FHIR 서버에 PUT 요청
            url = f"{self.base_url}/Patient/{patient_id}"
            headers = self._get_headers()

            response = self.session.put(
                url,
                json=updated_resource,
                headers=headers,
                timeout=10
            )

            # 응답 처리
            if response.status_code == 200:
                # 성공: 업데이트된 리소스 반환
                updated_patient = response.json()
                return True, updated_patient

            elif response.status_code == 400:
                # 유효성 검사 실패 (Bad Request)
                error_msg = self._parse_error_response(response)
                logger.warning(f"FHIR validation failed: {error_msg}")
                return False, {"error": error_msg}

            elif response.status_code == 404:
                # 환자 없음
                return False, {"error": f"Patient {patient_id} not found"}

            else:
                # 기타 오류 (서버 오류 등)
                error_msg = f"FHIR server error: {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except requests.ConnectionError as e:
            logger.error(f"FHIR connection error: {e}")
            raise Exception(f"Cannot connect to FHIR server: {e}")

        except requests.Timeout as e:
            logger.error(f"FHIR timeout: {e}")
            raise Exception(f"FHIR server timeout: {e}")

        except Exception as e:
            logger.error(f"FHIR adapter error: {e}")
            raise

    def _get_patient_resource(self, patient_id: str) -> Optional[Dict]:
        """FHIR 서버에서 Patient 리소스 조회"""
        try:
            url = f"{self.base_url}/Patient/{patient_id}"
            headers = self._get_headers()

            response = self.session.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()

            return None

        except Exception as e:
            logger.error(f"Failed to get patient resource: {e}")
            return None

    def _merge_patient_data(self, fhir_resource: Dict, update_data: Dict) -> Dict:
        """
        FHIR Patient 리소스에 업데이트 데이터 병합

        Django 필드 -> FHIR 필드 매핑:
        - phone -> telecom[0].value
        - email -> telecom[1].value
        - address -> address[0].text
        """
        # telecom 배열 초기화
        if 'telecom' not in fhir_resource:
            fhir_resource['telecom'] = []

        # 전화번호 업데이트
        if 'phone' in update_data:
            phone_entry = next(
                (t for t in fhir_resource['telecom'] if t.get('system') == 'phone'),
                None
            )
            if phone_entry:
                phone_entry['value'] = update_data['phone']
            else:
                fhir_resource['telecom'].append({
                    'system': 'phone',
                    'value': update_data['phone'],
                    'use': 'mobile'
                })

        # 이메일 업데이트
        if 'email' in update_data:
            email_entry = next(
                (t for t in fhir_resource['telecom'] if t.get('system') == 'email'),
                None
            )
            if email_entry:
                email_entry['value'] = update_data['email']
            else:
                fhir_resource['telecom'].append({
                    'system': 'email',
                    'value': update_data['email'],
                    'use': 'home'
                })

        # 주소 업데이트
        if 'address' in update_data:
            if 'address' not in fhir_resource:
                fhir_resource['address'] = []

            if fhir_resource['address']:
                fhir_resource['address'][0]['text'] = update_data['address']
            else:
                fhir_resource['address'].append({
                    'use': 'home',
                    'type': 'physical',
                    'text': update_data['address']
                })

        return fhir_resource

    def _get_headers(self) -> Dict:
        """HTTP 헤더 생성"""
        headers = {
            'Content-Type': 'application/fhir+json',
            'Accept': 'application/fhir+json'
        }

        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        return headers

    def _parse_error_response(self, response: requests.Response) -> str:
        """FHIR 서버 에러 응답 파싱"""
        try:
            error_data = response.json()

            # FHIR OperationOutcome 파싱
            if error_data.get('resourceType') == 'OperationOutcome':
                issues = error_data.get('issue', [])
                if issues:
                    return issues[0].get('diagnostics', 'Validation failed')

            return error_data.get('error', 'Unknown error')

        except Exception:
            return response.text or f"HTTP {response.status_code}"
