from rest_framework import serializers
from .models import LabTestMaster, LabResult

class LabTestMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTestMaster
        fields = '__all__'

class LabResultSerializer(serializers.ModelSerializer):
    """검사 결과 시리얼라이저"""
    test_name = serializers.ReadOnlyField(source='test_master.test_name')
    reference_range = serializers.ReadOnlyField(source='test_master.reference_range')

    class Meta:
        model = LabResult
        fields = [
            'result_id', 'order', 'patient', 'test_master', 'test_name',
            'result_value', 'result_unit', 'reference_range', 'result_details',
            'is_abnormal', 'abnormal_flag', 'reported_at', 'reported_by', 'version'
        ]
        read_only_fields = ['result_id', 'is_abnormal', 'abnormal_flag', 'reported_at', 'version']

class LabResultCreateSerializer(serializers.ModelSerializer):
    """검사 결과 등록용 시리얼라이저"""
    results = serializers.JSONField(write_only=True, required=False, help_text="상세 결과 데이터 (JSON)")

    class Meta:
        model = LabResult
        fields = [
            'order', 'patient', 'test_master', 'result_value', 'result_unit', 
            'reported_by', 'results', 'result_details'
        ]
