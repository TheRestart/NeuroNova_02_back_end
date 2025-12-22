"""
OpenEMR API 클라이언트
"""
import requests
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class OpenEMRClient:
    """OpenEMR REST API 클라이언트"""

    def __init__(self, base_url: str = "http://localhost:80"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token = None

    def health_check(self) -> Dict:
        """OpenEMR 서버 상태 확인"""
        try:
            response = self.session.get(f"{self.base_url}", timeout=5)
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "openemr_url": self.base_url
            }
        except requests.RequestException as e:
            logger.error(f"OpenEMR health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "openemr_url": self.base_url
            }

    def authenticate(self, username: str = "admin", password: str = "pass") -> Dict:
        """
        OpenEMR API 인증

        Note: 실제 프로덕션에서는 OAuth2 flow를 사용해야 합니다.
        개발/테스트 환경에서는 간단한 인증을 사용합니다.
        """
        try:
            # OpenEMR 7.0.3은 기본적으로 /api/auth 엔드포인트를 사용
            auth_url = f"{self.base_url}/apis/default/api/auth"

            payload = {
                "grant_type": "password",
                "username": username,
                "password": password,
                "scope": "openid api:fhir"
            }

            # 개발 환경에서는 인증 없이 진행 (OpenEMR 설정에 따라 다름)
            # 실제 환경에서는 OAuth2 token을 받아야 함

            response = self.session.post(auth_url, data=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                return {
                    "success": True,
                    "token": self.token
                }
            else:
                logger.warning(f"Auth failed: {response.status_code}")
                # 인증 실패해도 일부 API는 사용 가능할 수 있음
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": "Authentication not required or failed"
                }

        except requests.RequestException as e:
            logger.error(f"OpenEMR auth error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_patients(self, limit: int = 10) -> List[Dict]:
        """환자 목록 조회"""
        try:
            # OpenEMR FHIR API 사용
            url = f"{self.base_url}/apis/default/fhir/Patient"
            params = {"_count": limit}

            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'

            response = self.session.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # FHIR Bundle에서 환자 리소스 추출
                if data.get('entry'):
                    return [entry['resource'] for entry in data['entry']]
                return []
            else:
                logger.warning(f"Get patients failed: {response.status_code}")
                return []

        except requests.RequestException as e:
            logger.error(f"Get patients error: {e}")
            return []

    def search_patients(self, given: Optional[str] = None,
                       family: Optional[str] = None) -> List[Dict]:
        """환자 검색"""
        try:
            url = f"{self.base_url}/apis/default/fhir/Patient"
            params = {}

            if given:
                params['given'] = given
            if family:
                params['family'] = family

            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'

            response = self.session.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('entry'):
                    return [entry['resource'] for entry in data['entry']]
                return []
            else:
                return []

        except requests.RequestException as e:
            logger.error(f"Search patients error: {e}")
            return []

    def get_patient(self, patient_id: str) -> Optional[Dict]:
        """특정 환자 조회"""
        try:
            url = f"{self.base_url}/apis/default/fhir/Patient/{patient_id}"

            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'

            response = self.session.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Get patient {patient_id} failed: {response.status_code}")
                return None

        except requests.RequestException as e:
            logger.error(f"Get patient error: {e}")
            return None
