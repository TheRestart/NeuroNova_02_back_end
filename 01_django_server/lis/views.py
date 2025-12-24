from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import LabTestMaster, LabResult
from .serializers import (
    LabTestMasterSerializer, LabResultSerializer, LabResultCreateSerializer
)
from .services import LabResultService

class LabTestMasterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    검사 마스터 데이터 조회 API
    """
    queryset = LabTestMaster.objects.filter(is_active=True)
    serializer_class = LabTestMasterSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['test_code', 'test_name', 'sample_type']

class LabResultViewSet(viewsets.ModelViewSet):
    """
    검사 결과 CRUD API
    """
    queryset = LabResult.objects.all()
    serializer_class = LabResultSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return LabResultCreateSerializer
        return LabResultSerializer

    def create(self, request, *args, **kwargs):
        """검사 결과 등록 (Service 레이어 사용)"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = LabResultService.create_lab_result(serializer.validated_data)
            response_serializer = LabResultSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_patient(self, request):
        """특정 환자의 검사 이력 조회"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response({"error": "patient_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        results = LabResultService.get_patient_lab_history(patient_id)
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)
