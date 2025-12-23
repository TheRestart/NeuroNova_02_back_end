"""
CDSS 전역 예외 정의
"""


class CDSSException(Exception):
    """CDSS 시스템 기본 예외"""
    def __init__(self, message, status_code=400, error_code=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class OpenEMRException(CDSSException):
    """OpenEMR 연동 관련 예외"""
    def __init__(self, message, status_code=503):
        super().__init__(message, status_code, error_code='OPENEMR_ERROR')


class OrthancException(CDSSException):
    """Orthanc PACS 연동 관련 예외"""
    def __init__(self, message, status_code=503):
        super().__init__(message, status_code, error_code='ORTHANC_ERROR')


class RabbitMQException(CDSSException):
    """RabbitMQ 큐 연동 관련 예외"""
    def __init__(self, message, status_code=503):
        super().__init__(message, status_code, error_code='RABBITMQ_ERROR')


class AIServerException(CDSSException):
    """AI Server 연동 관련 예외"""
    def __init__(self, message, status_code=503):
        super().__init__(message, status_code, error_code='AI_SERVER_ERROR')


class AuthenticationException(CDSSException):
    """인증 관련 예외"""
    def __init__(self, message, status_code=401):
        super().__init__(message, status_code, error_code='AUTH_ERROR')


class AuthorizationException(CDSSException):
    """권한 관련 예외"""
    def __init__(self, message, status_code=403):
        super().__init__(message, status_code, error_code='PERMISSION_ERROR')


class ValidationException(CDSSException):
    """데이터 검증 관련 예외"""
    def __init__(self, message, status_code=400):
        super().__init__(message, status_code, error_code='VALIDATION_ERROR')


class ResourceNotFoundException(CDSSException):
    """리소스를 찾을 수 없는 경우"""
    def __init__(self, message, status_code=404):
        super().__init__(message, status_code, error_code='NOT_FOUND')


class ConflictException(CDSSException):
    """리소스 충돌 예외 (중복 등)"""
    def __init__(self, message, status_code=409):
        super().__init__(message, status_code, error_code='CONFLICT')
