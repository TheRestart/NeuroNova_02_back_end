from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    """감사 로그 시리얼라이저"""
    user_name = serializers.ReadOnlyField(source='user.full_name')
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_name', 'action', 'action_display',
            'app_label', 'model_name', 'object_id', 'change_summary',
            'previous_data', 'current_data', 'ip_address', 'user_agent',
            'path', 'created_at'
        ]
