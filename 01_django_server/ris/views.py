from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from django.utils import timezone
from datetime import datetime

from .models import RadiologyOrder, RadiologyStudy, RadiologyReport
from .serializers import RadiologyOrderSerializer, RadiologyStudySerializer, RadiologyReportSerializer
from .clients import OrthancClient


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
    client = OrthancClient()
    orthanc_studies = client.get_studies(limit=50)
    
    synced_count = 0
    for orthanc_study_id in orthanc_studies:
        try:
            # Orthanc Study 상세 정보 조회
            study_data = client.get_study(orthanc_study_id)
            metadata = client.get_study_metadata(orthanc_study_id)
            
            # DICOM 메타데이터 파싱
            patient_name = metadata.get('PatientName', 'Unknown')
            patient_id = metadata.get('PatientID', 'Unknown')
            study_date_str = metadata.get('StudyDate', '')
            study_time_str = metadata.get('StudyTime', '')
            study_instance_uid = metadata.get('StudyInstanceUID', orthanc_study_id)
            
            # 날짜/시간 변환
            study_date = None
            study_time = None
            if study_date_str:
                try:
                    study_date = datetime.strptime(study_date_str, '%Y%m%d').date()
                except ValueError:
                    pass
            if study_time_str:
                try:
                    # DICOM 시간 형식: HHMMSS.ffffff
                    time_parts = study_time_str.split('.')[0]
                    study_time = datetime.strptime(time_parts, '%H%M%S').time()
                except ValueError:
                    pass
            
            # Django DB에 저장/업데이트
            RadiologyStudy.objects.update_or_create(
                orthanc_study_id=orthanc_study_id,
                defaults={
                    'study_instance_uid': study_instance_uid,
                    'patient_name': patient_name,
                    'patient_id': patient_id,
                    'study_date': study_date,
                    'study_time': study_time,
                    'study_description': metadata.get('StudyDescription', ''),
                    'modality': metadata.get('Modality', ''),
                    'referring_physician': metadata.get('ReferringPhysicianName', ''),
                    'num_series': len(study_data.get('Series', [])),
                    'num_instances': len(study_data.get('Instances', [])),
                }
            )
            synced_count += 1
        except Exception as e:
            print(f"Failed to sync study {orthanc_study_id}: {e}")
            continue
    
    return Response({
        'message': f'Synced {synced_count} studies from Orthanc',
        'synced_count': synced_count
    })


class RadiologyOrderViewSet(viewsets.ModelViewSet):
    queryset = RadiologyOrder.objects.all()
    serializer_class = RadiologyOrderSerializer
    permission_classes = [AllowAny if not settings.ENABLE_SECURITY else IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(ordered_by=self.request.user if self.request.user.is_authenticated else None)


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
        
        report.status = 'FINAL'
        report.signed_at = timezone.now()
        report.signed_by = request.user if request.user.is_authenticated else None
        report.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)
