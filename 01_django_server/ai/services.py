from django.utils import timezone
from .models import AIJob
from .queue_client import AIQueueClient

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
