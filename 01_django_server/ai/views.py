from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings

from .models import AIJob
from .serializers import AIJobSerializer
from .services import AIJobService


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
    metadata = request.data.get('metadata')

    # Service 레이어 사용
    service = AIJobService()
    ai_job = service.submit_ai_job(study_id, model_type, metadata)

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
