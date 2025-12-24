from django.utils import timezone
from .models import AIJob
from .queue_client import AIQueueClient
from acct.services import AlertService
from audit.services import AuditService

class AIJobService:
    def submit_ai_job(self, study_id, model_type, metadata=None):
        if not study_id:
            raise ValueError('study_id is required')
            
        # AI Job 생성
        ai_job = AIJob.objects.create(
            study_id=study_id,
            model_type=model_type,
            status='QUEUED',
            queued_at=timezone.now()
        )
        
        # RabbitMQ 큐에 추가
        job_data = {
            'job_id': str(ai_job.job_id),
            'study_id': str(study_id),
            'model_type': model_type,
            'created_at': ai_job.created_at.isoformat()
        }
        
        if metadata:
            job_data['metadata'] = metadata
        
        try:
            with AIQueueClient() as queue_client:
                success = queue_client.publish_ai_job(job_data)
            
            if not success:
                ai_job.status = 'FAILED'
                ai_job.error_message = 'Failed to publish to RabbitMQ'
                ai_job.save()
            
        except Exception as e:
            ai_job.status = 'FAILED'
            ai_job.error_message = str(e)
            ai_job.save()
            
        return ai_job

    def update_job_result(self, job_id, status, result_data=None, error_message=None):
        """AI 서버로부터 분석 결과를 수신하여 업데이트 (Callback)"""
        try:
            ai_job = AIJob.objects.get(job_id=job_id)
            ai_job.status = status
            if result_data:
                ai_job.result_data = result_data
            if error_message:
                ai_job.error_message = error_message
            
            if status == 'COMPLETED':
                ai_job.completed_at = timezone.now()
                # 의료진에게 실시간 알림 발송 (역할 기반)
                # AlertService.send_role_alert(role, message, alert_type='INFO', metadata=None)
                AlertService.send_role_alert(
                    role='doctor',
                    message=f"환자 연구({ai_job.study_id}) AI 분석 완료. 검토 요망.",
                    alert_type='INFO',
                    metadata={'job_id': str(job_id), 'source': 'AI'}
                )
            
            ai_job.save()
            
            # 감사 로그 기록
            AuditService.log_action(
                user=None,
                action='UPDATE',
                app_label='ai',
                model_name='AIJob',
                object_id=job_id,
                change_summary=f"AI 분석 결과 수신: {status}",
                current_data={'status': status, 'is_callback': True}
            )
            return ai_job
        except AIJob.DoesNotExist:
            return None

    def review_job(self, job_id, user, status, comment=None):
        """의료진의 분석 결과 검토 (승인/반려)"""
        try:
            ai_job = AIJob.objects.get(job_id=job_id)
            ai_job.review_status = status
            ai_job.reviewed_by = user
            ai_job.reviewed_at = timezone.now()
            if comment:
                ai_job.review_comment = comment
            ai_job.save()
            
            # 감사 로그 기록
            AuditService.log_action(
                user=user,
                action='UPDATE',
                app_label='ai',
                model_name='AIJob',
                object_id=job_id,
                change_summary=f"AI 분석 결과 검토: {status}",
                current_data={'review_status': status, 'comment': comment}
            )
            return ai_job
        except AIJob.DoesNotExist:
            return None
