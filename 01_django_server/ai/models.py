import uuid
from django.db import models


class AIJob(models.Model):
    """AI 분석 작업"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('QUEUED', 'Queued'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    study_id = models.UUIDField(help_text="RadiologyStudy FK")
    model_type = models.CharField(max_length=50, help_text="AI 모델 종류 (e.g., tumor_detection)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # 결과 (COMPLETED 상태일 때)
    result_data = models.JSONField(null=True, blank=True, help_text="AI 분석 결과")
    error_message = models.TextField(blank=True, help_text="실패 시 에러 메시지")
    
    # 의료진 검토 (Review/Approval)
    REVIEW_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    review_status = models.CharField(max_length=20, choices=REVIEW_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(
        'acct.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_ai_jobs'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True, help_text="의료진 검토 의견")
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    queued_at = models.DateTimeField(null=True, blank=True, help_text="RabbitMQ 큐 추가 시간")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['study_id']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"AI Job {self.job_id} - {self.status}"
