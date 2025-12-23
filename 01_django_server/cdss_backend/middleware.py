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
