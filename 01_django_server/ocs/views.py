from rest_framework import viewsets, filters
from .models import MedicationMaster, DiagnosisMaster
from .serializers import MedicationMasterSerializer, DiagnosisMasterSerializer

class MedicationMasterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    약물 마스터 데이터 조회 API
    """
    queryset = MedicationMaster.objects.filter(is_active=True)
    serializer_class = MedicationMasterSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['drug_code', 'drug_name', 'generic_name']

class DiagnosisMasterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    진단 마스터 데이터 조회 API
    """
    queryset = DiagnosisMaster.objects.filter(is_active=True)
    serializer_class = DiagnosisMasterSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['diag_code', 'name_ko', 'name_en']
