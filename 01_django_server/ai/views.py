from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
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


@api_view(['POST'])
@permission_classes([AllowAny])  # AI 서버에서의 접근 허용 (필요 시 IP 화이트리스트 적용)
def ai_callback(request):
    """AI 서버로부터 분석 결과를 수신하는 콜백 엔드포인트"""
    job_id = request.data.get('job_id')
    status_val = request.data.get('status')
    result_data = request.data.get('result')
    error_message = request.data.get('error')

    if not job_id or not status_val:
        return Response({'error': 'job_id and status are required'}, status=status.HTTP_400_BAD_REQUEST)

    service = AIJobService()
    ai_job = service.update_job_result(job_id, status_val, result_data, error_message)

    if ai_job:
        return Response({'status': 'success'})
    return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)


class AIJobViewSet(viewsets.ReadOnlyModelViewSet):
    """AI Job 조회 및 승인/반려"""
    queryset = AIJob.objects.all()
    serializer_class = AIJobSerializer
    permission_classes = [AllowAny if not settings.ENABLE_SECURITY else IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        study_id = self.request.query_params.get('study_id')
        if study_id:
            queryset = queryset.filter(study_id=study_id)
        return queryset

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """의료진의 분석 결과 승인/반려"""
        ai_job = self.get_object()
        review_status = request.data.get('status')  # 'APPROVED' or 'REJECTED'
        comment = request.data.get('comment', '')

        if review_status not in ['APPROVED', 'REJECTED']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        service = AIJobService()
        updated_job = service.review_job(ai_job.job_id, request.user, review_status, comment)

        if updated_job:
            return Response(self.get_serializer(updated_job).data)
        return Response({'error': 'Failed to update job'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
