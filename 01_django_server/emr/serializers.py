"""
EMR Serializers

Django REST Framework용 시리얼라이저
"""

from rest_framework import serializers
from .models import PatientCache, Encounter, EncounterDiagnosis, Order, OrderItem


class PatientCacheSerializer(serializers.ModelSerializer):
    """환자 캐시 시리얼라이저"""
    full_name = serializers.ReadOnlyField()
    is_synced = serializers.ReadOnlyField()

    class Meta:
        model = PatientCache
        fields = [
            'patient_id', 'family_name', 'given_name', 'birth_date', 'gender',
            'phone', 'email', 'address', 'emergency_contact', 'allergies',
            'blood_type', 'openemr_patient_id', 'last_synced_at',
            'created_at', 'updated_at', 'full_name', 'is_synced'
        ]
        read_only_fields = ['patient_id', 'created_at', 'updated_at']


class PatientCreateSerializer(serializers.ModelSerializer):
    """환자 생성 시리얼라이저"""

    class Meta:
        model = PatientCache
        fields = [
            'family_name', 'given_name', 'birth_date', 'gender',
            'phone', 'email', 'address', 'emergency_contact', 'allergies', 'blood_type'
        ]



class EncounterDiagnosisSerializer(serializers.ModelSerializer):
    """진료 진단 시리얼라이저"""
    class Meta:
        model = EncounterDiagnosis
        fields = ['diag_code', 'diagnosis_name', 'priority', 'created_at']


class EncounterSerializer(serializers.ModelSerializer):
    """진료 기록 시리얼라이저"""
    patient_name = serializers.SerializerMethodField()
    diagnoses = EncounterDiagnosisSerializer(many=True, read_only=True)

    class Meta:
        model = Encounter
        fields = [
            'encounter_id', 'patient', 'patient_name', 'doctor_id',
            'encounter_type', 'department', 'chief_complaint', 'diagnosis',
            'status', 'encounter_date', 'diagnoses', 'created_at', 'updated_at'
        ]
        read_only_fields = ['encounter_id', 'created_at', 'updated_at']

    def get_patient_name(self, obj):
        return obj.patient.full_name


class EncounterCreateSerializer(serializers.ModelSerializer):
    """진료 기록 생성 시리얼라이저"""
    diagnosis_codes = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Encounter
        fields = [
            'patient', 'doctor_id', 'encounter_type', 'department',
            'chief_complaint', 'diagnosis', 'diagnosis_codes', 'status', 'encounter_date'
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    """처방 항목 시리얼라이저"""
    master_info = serializers.JSONField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'item_id', 'drug_code', 'drug_name', 'dosage',
            'frequency', 'duration', 'route', 'instructions', 'master_info'
        ]
        read_only_fields = ['item_id']


class OrderSerializer(serializers.ModelSerializer):
    """처방 시리얼라이저 (조회용)"""
    items = OrderItemSerializer(many=True, read_only=True)
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'order_id', 'patient', 'patient_name', 'encounter', 'ordered_by',
            'order_type', 'urgency', 'status', 'notes',
            'ordered_at', 'executed_at', 'executed_by', 'items'
        ]
        read_only_fields = ['order_id', 'ordered_at']

    def get_patient_name(self, obj):
        return obj.patient.full_name


class OrderCreateSerializer(serializers.ModelSerializer):
    """처방 생성 시리얼라이저"""
    order_items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Order
        fields = [
            'patient', 'encounter', 'ordered_by', 'order_type',
            'urgency', 'status', 'notes', 'order_items'
        ]


class OrderItemUpdateSerializer(serializers.ModelSerializer):
    """처방 항목 수정 시리얼라이저"""

    class Meta:
        model = OrderItem
        fields = [
            'drug_code', 'drug_name', 'dosage',
            'frequency', 'duration', 'route', 'instructions'
        ]
