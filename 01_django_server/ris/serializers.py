from rest_framework import serializers
from .models import RadiologyOrder, RadiologyStudy, RadiologyReport


class RadiologyOrderSerializer(serializers.ModelSerializer):
    ordered_by_username = serializers.CharField(source='ordered_by.username', read_only=True)
    
    class Meta:
        model = RadiologyOrder
        fields = [
            'order_id', 'patient_id', 'ordered_by', 'ordered_by_username',
            'modality', 'body_part', 'clinical_info', 'status', 'priority',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['order_id', 'created_at', 'updated_at']


class RadiologyStudySerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source='order.order_id', read_only=True, allow_null=True)
    
    class Meta:
        model = RadiologyStudy
        fields = [
            'study_id', 'order', 'order_id', 'orthanc_study_id', 'study_instance_uid',
            'patient_name', 'patient_id', 'study_date', 'study_time',
            'study_description', 'modality', 'referring_physician',
            'num_series', 'num_instances', 'created_at', 'synced_at'
        ]
        read_only_fields = ['study_id', 'created_at', 'synced_at']


class RadiologyReportSerializer(serializers.ModelSerializer):
    radiologist_name = serializers.CharField(source='radiologist.username', read_only=True)
    signed_by_name = serializers.CharField(source='signed_by.username', read_only=True, allow_null=True)
    study_patient_name = serializers.CharField(source='study.patient_name', read_only=True)
    
    class Meta:
        model = RadiologyReport
        fields = [
            'report_id', 'study', 'study_patient_name', 'radiologist', 'radiologist_name',
            'findings', 'impression', 'status', 'signed_at', 'signed_by', 'signed_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['report_id', 'created_at', 'updated_at', 'signed_at', 'signed_by']
