from rest_framework import serializers
from .models import MedicationMaster, DiagnosisMaster

class MedicationMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationMaster
        fields = '__all__'

class DiagnosisMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosisMaster
        fields = '__all__'
