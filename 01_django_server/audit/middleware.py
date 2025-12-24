import json
import logging
from .services import AuditService

logger = logging.getLogger(__name__)

class AuditMiddleware:
    """
    모든 데이터 변경 요청을 자동으로 기록하는 감사 미들웨어
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. 대상 메서드 확인 (변경이 발생하는 메서드만 기록)
        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return self.get_response(request)

        # 2. 특정 경로는 제외 (예: 로그인, 로그아웃, 헬스체크 등)
        exempt_paths = ['/api/acct/login/', '/api/acct/logout/', '/api/emr/health/']
        if any(request.path.startswith(path) for path in exempt_paths):
            return self.get_response(request)

        # 3. 요청 데이터 미리 추출 (request.body는 한번만 읽을 수 있으므로 주의)
        # DRF의 경우 request.data를 사용하므로, 미들웨어 수준에서는 logging이 까다로움
        # 여기서는 경로와 사용자 정보를 기본으로 기록하고, 상세 데이터는 Service 레이어에서 명시적으로 기록 권장
        
        response = self.get_response(request)

        # 4. 성공적인 처리(또는 특정 에러) 후 로그 기록
        if response.status_code >= 200 and response.status_code < 500:
            # 앱 라벨 및 모델 명 추출 시도 (간단한 규칙 기반)
            path_parts = request.path.strip('/').split('/')
            app_label = path_parts[1] if len(path_parts) > 1 else 'unknown'
            model_name = path_parts[2] if len(path_parts) > 2 else 'unknown'
            
            # 액션 매핑
            action_map = {
                'POST': 'CREATE',
                'PUT': 'UPDATE',
                'PATCH': 'UPDATE',
                'DELETE': 'DELETE'
            }
            action = action_map.get(request.method, 'ACCESS')

            # 로그 기록 요청 (비동기 처리 권장되나 여기서는 동기 처리)
            AuditService.log_action(
                user=request.user,
                action=action,
                app_label=app_label,
                model_name=model_name,
                path=request.path,
                request=request
            )

        return response
