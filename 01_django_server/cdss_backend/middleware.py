"""
CDSS 전역 예외 처리 미들웨어
"""
import logging
import traceback
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.exceptions import APIException
from rest_framework import status

from .exceptions import CDSSException

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware:
    """
    전역 예외 처리 미들웨어
    모든 예외를 일관된 JSON 형식으로 반환
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """
        예외 발생 시 처리
        """
        # CDSS 커스텀 예외
        if isinstance(exception, CDSSException):
            logger.error(
                f"CDSS Exception: {exception.message}",
                extra={
                    'error_code': exception.error_code,
                    'status_code': exception.status_code,
                    'path': request.path,
                    'method': request.method,
                    'user': str(request.user) if hasattr(request, 'user') else 'Anonymous'
                }
            )
            return JsonResponse(
                {
                    'error': exception.message,
                    'error_code': exception.error_code,
                    'status_code': exception.status_code
                },
                status=exception.status_code
            )
        
        # Django REST Framework 예외
        if isinstance(exception, APIException):
            logger.error(
                f"API Exception: {str(exception)}",
                extra={
                    'status_code': exception.status_code,
                    'path': request.path,
                    'method': request.method
                }
            )
            return JsonResponse(
                {
                    'error': str(exception.detail) if hasattr(exception, 'detail') else str(exception),
                    'error_code': 'API_ERROR',
                    'status_code': exception.status_code
                },
                status=exception.status_code
            )
        
        # Django 기본 예외들
        if isinstance(exception, Http404):
            logger.warning(f"404 Not Found: {request.path}")
            return JsonResponse(
                {
                    'error': 'Resource not found',
                    'error_code': 'NOT_FOUND',
                    'status_code': 404
                },
                status=404
            )
        
        if isinstance(exception, PermissionDenied):
            logger.warning(
                f"Permission Denied: {request.path}",
                extra={'user': str(request.user) if hasattr(request, 'user') else 'Anonymous'}
            )
            return JsonResponse(
                {
                    'error': 'Permission denied',
                    'error_code': 'PERMISSION_DENIED',
                    'status_code': 403
                },
                status=403
            )
        
        if isinstance(exception, DjangoValidationError):
            logger.warning(f"Validation Error: {str(exception)}")
            return JsonResponse(
                {
                    'error': str(exception),
                    'error_code': 'VALIDATION_ERROR',
                    'status_code': 400
                },
                status=400
            )
        
        # 기타 모든 예외 (500 Internal Server Error)
        logger.error(
            f"Unhandled Exception: {str(exception)}",
            extra={
                'path': request.path,
                'method': request.method,
                'traceback': traceback.format_exc()
            }
        )
        
        # 프로덕션 환경에서는 상세 에러 메시지 숨김
        from django.conf import settings
        if settings.DEBUG:
            error_message = str(exception)
            error_traceback = traceback.format_exc()
        else:
            error_message = 'Internal server error'
            error_traceback = None
        
        response_data = {
            'error': error_message,
            'error_code': 'INTERNAL_ERROR',
            'status_code': 500
        }
        
        if error_traceback:
            response_data['traceback'] = error_traceback
        
        return JsonResponse(response_data, status=500)


class IdempotencyMiddleware:
    """
    중복 요청 방지를 위한 멱등성 미들웨어
    - X-Idempotency-Key 헤더가 있는 경우 작동
    - POST, PUT, PATCH, DELETE 요청에만 적용
    - 캐시를 사용하여 기존 응답을 저장하고 재활용
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. 멱등성 검사 대상 메서드인지 확인
        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return self.get_response(request)

        # 2. 멱등성 키 헤더 추출
        idempotency_key = request.headers.get('X-Idempotency-Key')
        if not idempotency_key:
            return self.get_response(request)

        # 3. 캐시 로드
        from django.core.cache import cache
        import hashlib
        
        # 키 생성 (사용자 ID + 키 + 경로)
        user_id = getattr(request.user, 'user_id', 'anonymous')
        cache_key = f"idempotency_{hashlib.md5(f'{user_id}:{idempotency_key}:{request.path}'.encode()).hexdigest()}"

        # 4. 이미 처리 중이거나 처리된 결과가 있는지 확인 (Locking/Caching)
        cached_response = cache.get(cache_key)
        if cached_response:
            if cached_response == 'PROCESSING':
                return JsonResponse(
                    {"error": "Request is already being processed"},
                    status=status.HTTP_409_CONFLICT
                )
            
            # 캐시된 응답 반환
            logger.info(f"Returning idempotent response for key: {idempotency_key}")
            return JsonResponse(
                cached_response['data'],
                status=cached_response['status']
            )

        # 5. 처리 중임을 표시 (2분간 유효)
        cache.set(cache_key, 'PROCESSING', timeout=120)

        # 6. 실제 로직 실행
        try:
            response = self.get_response(request)
            
            # 7. 성공적인 응답(2xx)은 캐싱 (5분간 유효)
            if 200 <= response.status_code < 300:
                # JsonResponse인 경우에만 데이터 추출 가능
                if isinstance(response, JsonResponse):
                    import json
                    response_data = json.loads(response.content)
                    cache.set(cache_key, {
                        'data': response_data,
                        'status': response.status_code
                    }, timeout=300)
            else:
                # 에러 발생 시에는 캐시 삭제 (재시도 가능하게)
                cache.delete(cache_key)
                
            return response

        except Exception as e:
            # 예외 발생 시 캐시 삭제
            cache.delete(cache_key)
            raise e
