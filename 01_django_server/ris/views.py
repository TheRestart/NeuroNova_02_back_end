from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings

from .models import RadiologyOrder, RadiologyStudy, RadiologyReport
from .serializers import RadiologyOrderSerializer, RadiologyStudySerializer, RadiologyReportSerializer
from .services import RadiologyOrderService, RadiologyStudyService, RadiologyReportService
from .clients.orthanc_client import OrthancClient


@api_view(['GET'])
@permission_classes([AllowAny])  # 개발 모드
def orthanc_health_check(request):
    """Orthanc 서버 연결 상태 확인"""
    client = OrthancClient()
    result = client.health_check()
    return Response(result)


@api_view(['GET'])
@permission_classes([AllowAny if not settings.ENABLE_SECURITY else IsAuthenticated])
def sync_orthanc_studies(request):
    """Orthanc에서 Study 목록을 가져와 Django DB에 동기화"""
    service = RadiologyStudyService()
    result = service.sync_studies_from_orthanc()

    return Response({
        'message': f"Synced {result['synced_count']} studies from Orthanc",
        'synced_count': result['synced_count'],
        'total': result['total']
    })


class RadiologyOrderViewSet(viewsets.ModelViewSet):
    queryset = RadiologyOrder.objects.all()
    serializer_class = RadiologyOrderSerializer
    permission_classes = [AllowAny if not settings.ENABLE_SECURITY else IsAuthenticated]
    
    def perform_create(self, serializer):
        # Service 레이어 사용
        user = self.request.user if self.request.user.is_authenticated else None
        RadiologyOrderService.create_order(serializer.validated_data, user)


class RadiologyStudyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RadiologyStudy.objects.all()
    serializer_class = RadiologyStudySerializer
    permission_classes = [AllowAny if not settings.ENABLE_SECURITY else IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """환자 이름 또는 ID로 Study 검색"""
        patient_name = request.query_params.get('patient_name')
        patient_id = request.query_params.get('patient_id')
        
        queryset = self.get_queryset()
        if patient_name:
            queryset = queryset.filter(patient_name__icontains=patient_name)
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        serializer = self.get_serializer(queryset[:20], many=True)
        return Response(serializer.data)


class RadiologyReportViewSet(viewsets.ModelViewSet):
    queryset = RadiologyReport.objects.all()
    serializer_class = RadiologyReportSerializer
    permission_classes = [AllowAny if not settings.ENABLE_SECURITY else IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(radiologist=self.request.user if self.request.user.is_authenticated else None)

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """판독문 서명"""
        report = self.get_object()

        if report.status == 'FINAL':
            return Response(
                {'error': 'Report already finalized'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Service 레이어 사용
        service = RadiologyReportService()
        user = request.user if request.user.is_authenticated else None
        report = service.sign_report(report.report_id, user)

        serializer = self.get_serializer(report)
        return Response(serializer.data)
