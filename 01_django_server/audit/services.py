import logging
from .models import AuditLog

logger = logging.getLogger(__name__)

class AuditService:
    """시스템 감사 로그 서비스"""

    @staticmethod
    def log_action(user, action, app_label, model_name, object_id=None, 
                   change_summary=None, previous_data=None, current_data=None,
                   request=None):
        """
        감사 로그 기록
        """
        ip_address = None
        user_agent = None
        path = None

        if request:
            # Request 객체에서 메타데이터 추출
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT')
            path = request.path

        try:
            log_entry = AuditLog.objects.create(
                user=user if user and user.is_authenticated else None,
                action=action,
                app_label=app_label,
                model_name=model_name,
                object_id=str(object_id) if object_id else None,
                change_summary=change_summary,
                previous_data=previous_data,
                current_data=current_data,
                ip_address=ip_address,
                user_agent=user_agent,
                path=path
            )
            return log_entry
        except Exception as e:
            logger.error(f"Failed to record audit log: {str(e)}")
            return None

    @staticmethod
    def get_logs_by_user(user_id):
        """사용자별 로그 조회"""
        return AuditLog.objects.filter(user_id=user_id).order_by('-created_at')

    @staticmethod
    def get_logs_by_model(app_label, model_name, object_id=None):
        """특정 모델/객체별 로그 조회"""
        queryset = AuditLog.objects.filter(app_label=app_label, model_name=model_name)
        if object_id:
            queryset = queryset.filter(object_id=str(object_id))
        return queryset.order_by('-created_at')
