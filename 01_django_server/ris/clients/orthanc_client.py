import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class OrthancClient:
    """Orthanc DICOM 서버 클라이언트"""
    
    def __init__(self):
        self.base_url = settings.ORTHANC_API_URL
        self.auth = (settings.ORTHANC_USERNAME, settings.ORTHANC_PASSWORD)
    
    def health_check(self):
        """Orthanc 서버 연결 확인"""
        try:
            url = f"{self.base_url}/system"
            response = requests.get(url, auth=self.auth, timeout=5)
            response.raise_for_status()
            return {'status': 'healthy', 'data': response.json()}
        except requests.RequestException as e:
            logger.error(f"Orthanc health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}
    
    def get_studies(self, limit=100, since=0):
        """모든 Study 목록 조회"""
        try:
            url = f"{self.base_url}/studies"
            params = {'limit': limit, 'since': since}
            response = requests.get(url, auth=self.auth, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get studies: {e}")
            return []
    
    def get_study(self, study_id):
        """Study 상세 정보 조회"""
        try:
            url = f"{self.base_url}/studies/{study_id}"
            response = requests.get(url, auth=self.auth, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get study {study_id}: {e}")
            raise
    
    def get_study_metadata(self, study_id):
        """Study의 DICOM 메타데이터 조회"""
        try:
            # Study의 첫 번째 Instance에서 메타데이터 추출
            study_data = self.get_study(study_id)
            if 'Instances' in study_data and len(study_data['Instances']) > 0:
                instance_id = study_data['Instances'][0]
                url = f"{self.base_url}/instances/{instance_id}/simplified-tags"
                response = requests.get(url, auth=self.auth, timeout=10)
                response.raise_for_status()
                return response.json()
            return {}
        except requests.RequestException as e:
            logger.error(f"Failed to get study metadata {study_id}: {e}")
            return {}
    
    def search_studies(self, patient_name=None, patient_id=None, study_date=None):
        """DICOM Query/Retrieve로 Study 검색"""
        try:
            url = f"{self.base_url}/tools/find"
            query = {"Level": "Study", "Query": {}, "Expand": True}
            
            if patient_name:
                query["Query"]["PatientName"] = f"*{patient_name}*"
            if patient_id:
                query["Query"]["PatientID"] = patient_id
            if study_date:
                query["Query"]["StudyDate"] = study_date
                
            response = requests.post(url, json=query, auth=self.auth, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to search studies: {e}")
            return []
    
    def download_dicom_instance(self, instance_id):
        """DICOM 인스턴스 파일 다운로드"""
        try:
            url = f"{self.base_url}/instances/{instance_id}/file"
            response = requests.get(url, auth=self.auth, timeout=30)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"Failed to download instance {instance_id}: {e}")
            raise
    
    def get_study_instances(self, study_id):
        """Study의 모든 Instance ID 목록"""
        try:
            study_data = self.get_study(study_id)
            return study_data.get('Instances', [])
        except Exception as e:
            logger.error(f"Failed to get instances for study {study_id}: {e}")
            return []
