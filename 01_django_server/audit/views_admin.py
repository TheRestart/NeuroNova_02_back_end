from django.shortcuts import render
from .models import AuditLog

def log_viewer(request):
    """관리자용 감사 로그 뷰어"""
    # 쿼리 파라미터를 통한 필터링
    action = request.GET.get('action')
    app_label = request.GET.get('app')
    user_id = request.GET.get('user')
    
    logs = AuditLog.objects.all().order_by('-created_at')
    
    if action:
        logs = logs.filter(action=action)
    if app_label:
        logs = logs.filter(app_label=app_label)
    if user_id:
        logs = logs.filter(user_id=user_id)
        
    # 간단한 페이지네이션 (상위 100개만 표시)
    logs = logs[:100]
    
    context = {
        'logs': logs,
        'count': logs.count(),
        'actions': AuditLog.objects.values_list('action', flat=True).distinct(),
        'apps': AuditLog.objects.values_list('app_label', flat=True).distinct(),
    }
    return render(request, 'audit/log_viewer.html', context)
