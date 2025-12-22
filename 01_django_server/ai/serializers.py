from rest_framework import serializers
from .models import AIJob


class AIJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIJob
        fields = [
            'job_id', 'study_id', 'model_type', 'status',
            'result_data', 'error_message',
            'created_at', 'queued_at', 'started_at', 'completed_at'
        ]
        read_only_fields = [
            'job_id', 'status', 'result_data', 'error_message',
            'created_at', 'queued_at', 'started_at', 'completed_at'
        ]
