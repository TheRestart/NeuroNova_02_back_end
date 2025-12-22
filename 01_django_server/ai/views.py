from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from django.utils import timezone

from .models import AIJob
from .serializers import AIJobSerializer
from .queue_client import AIQueueClient


@api_view(['POST'])
@permission_classes([AllowAny if not settings.ENABLE_SECURITY else IsAuthenticated])
def submit_ai_job(request):
    """AI 분석 작업 제출 (RabbitMQ 큐에 추가)
    
    Request Body:
        {
            "study_id": "uuid",
            "model_type": "tumor_detection"
        }
    """
    study_id = request.data.get('study_id')
    model_type = request.data.get('model_type', 'tumor_detection')
    
    if not study_id:
        return Response(
            {'error': 'study_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
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
    
    try:
        with AIQueueClient() as queue_client:
            success = queue_client.publish_ai_job(job_data)
        
        if not success:
            ai_job.status = 'FAILED'
            ai_job.error_message = 'Failed to publish to RabbitMQ'
            ai_job.save()
            return Response(
                {'error': 'Failed to queue AI job'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        ai_job.status = 'FAILED'
        ai_job.error_message = str(e)
        ai_job.save()
        return Response(
            {'error': f'RabbitMQ error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    serializer = AIJobSerializer(ai_job)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


class AIJobViewSet(viewsets.ReadOnlyModelViewSet):
    """AI Job 조회 (제출은 submit_ai_job 사용)"""
    queryset = AIJob.objects.all()
    serializer_class = AIJobSerializer
    permission_classes = [AllowAny if not settings.ENABLE_SECURITY else IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        study_id = self.request.query_params.get('study_id')
        if study_id:
            queryset = queryset.filter(study_id=study_id)
        return queryset
