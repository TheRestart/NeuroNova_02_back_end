"""
AI Repository Layer
데이터베이스 접근 로직
"""
from django.db import transaction
from .models import AIJob


class AIJobRepository:
    """AI Job Repository"""

    @staticmethod
    def get_all():
        """모든 AI Job 조회"""
        return AIJob.objects.all()

    @staticmethod
    def get_by_id(job_id):
        """ID로 AI Job 조회"""
        return AIJob.objects.get(job_id=job_id)

    @staticmethod
    def get_by_study_id(study_id):
        """Study ID로 AI Job 조회"""
        return AIJob.objects.filter(study_id=study_id)

    @staticmethod
    def get_by_status(status):
        """상태로 AI Job 조회"""
        return AIJob.objects.filter(status=status)

    @staticmethod
    def get_pending_jobs():
        """대기 중인 Job 조회"""
        return AIJob.objects.filter(status='PENDING')

    @staticmethod
    @transaction.atomic
    def create(data):
        """새 AI Job 생성"""
        return AIJob.objects.create(**data)

    @staticmethod
    @transaction.atomic
    def update(job_id, data):
        """AI Job 업데이트"""
        job = AIJob.objects.get(job_id=job_id)
        for key, value in data.items():
            setattr(job, key, value)
        job.save()
        return job

    @staticmethod
    @transaction.atomic
    def update_status(job_id, status, **extra_data):
        """상태 업데이트 (추가 필드 포함)"""
        job = AIJob.objects.get(job_id=job_id)
        job.status = status
        for key, value in extra_data.items():
            setattr(job, key, value)
        job.save()
        return job

    @staticmethod
    @transaction.atomic
    def delete(job_id):
        """AI Job 삭제"""
        job = AIJob.objects.get(job_id=job_id)
        job.delete()
