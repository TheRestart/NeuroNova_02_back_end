from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    """
    전수 감사 로그 (UC09)
    - 사용자 활동, 데이터 변경, API 접근 기록 저장
    """
    ACTION_CHOICES = [
        ('CREATE', '생성'),
        ('UPDATE', '수정'),
        ('DELETE', '삭제'),
        ('LOGIN', '로그인'),
        ('LOGOUT', '로그아웃'),
        ('ACCESS', '접근'),
        ('DOWNLOAD', '다운로드'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text="활동 사용자"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, help_text="행위")
    app_label = models.CharField(max_length=100, help_text="대상 앱 (예: emr, ocs)")
    model_name = models.CharField(max_length=100, help_text="대상 모델")
    object_id = models.CharField(max_length=100, blank=True, null=True, help_text="대상 객체 ID")
    
    change_summary = models.TextField(blank=True, null=True, help_text="변경 요약 (예: [이름] 홍길동 -> 김철수)")
    previous_data = models.JSONField(blank=True, null=True, help_text="변경 전 데이터")
    current_data = models.JSONField(blank=True, null=True, help_text="변경 후 데이터")
    
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text="접속 IP")
    user_agent = models.TextField(blank=True, null=True, help_text="브라우저 정보")
    path = models.TextField(blank=True, null=True, help_text="API 경로")
    
    created_at = models.DateTimeField(auto_now_add=True, help_text="발생 일시")

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['app_label', 'model_name']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"[{self.get_action_display()}] {self.user} - {self.app_label}.{self.model_name} at {self.created_at}"
