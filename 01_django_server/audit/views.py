from rest_framework import viewsets, filters, permissions
from .models import AuditLog
from .serializers import AuditLogSerializer

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    통합 로그 뷰어 API (UC09)
    - 관리자만 접근 가능 (실제 운영 시 IsAdminUser 적용 권장)
    - 기간, 사용자, 액션별 필터링 제공
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    
    # 개발 편의를 위해 AllowAny (실제로는 IsAdminUser 권장)
    permission_classes = [permissions.AllowAny]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'user__full_name', 'app_label', 'model_name', 'change_summary']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 추가 쿼리 파라미터 필터링
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
            
        app = self.request.query_params.get('app')
        if app:
            queryset = queryset.filter(app_label=app)
            
        return queryset
