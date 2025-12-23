"""
RIS Repository Layer
데이터베이스 접근 로직
"""
from django.db import transaction
from .models import RadiologyOrder, RadiologyStudy, RadiologyReport


class RadiologyOrderRepository:
    """영상 검사 오더 Repository"""
    
    @staticmethod
    def get_all():
        """모든 오더 조회"""
        return RadiologyOrder.objects.select_related('ordered_by').all()
    
    @staticmethod
    def get_by_id(order_id):
        """ID로 오더 조회"""
        return RadiologyOrder.objects.select_related('ordered_by').get(order_id=order_id)
    
    @staticmethod
    def get_by_patient_id(patient_id):
        """환자 ID로 오더 조회"""
        return RadiologyOrder.objects.filter(patient_id=patient_id).select_related('ordered_by')
    
    @staticmethod
    def get_by_status(status):
        """상태로 오더 조회"""
        return RadiologyOrder.objects.filter(status=status).select_related('ordered_by')
    
    @staticmethod
    @transaction.atomic
    def create(data):
        """새 오더 생성"""
        return RadiologyOrder.objects.create(**data)
    
    @staticmethod
    @transaction.atomic
    def update(order_id, data):
        """오더 업데이트"""
        order = RadiologyOrder.objects.get(order_id=order_id)
        for key, value in data.items():
            setattr(order, key, value)
        order.save()
        return order
    
    @staticmethod
    @transaction.atomic
    def delete(order_id):
        """오더 삭제"""
        order = RadiologyOrder.objects.get(order_id=order_id)
        order.delete()


class RadiologyStudyRepository:
    """DICOM Study Repository"""
    
    @staticmethod
    def get_all():
        """모든 Study 조회"""
        return RadiologyStudy.objects.select_related('order').all()
    
    @staticmethod
    def get_by_id(study_id):
        """ID로 Study 조회"""
        return RadiologyStudy.objects.select_related('order').get(study_id=study_id)
    
    @staticmethod
    def get_by_orthanc_id(orthanc_study_id):
        """Orthanc Study ID로 조회"""
        return RadiologyStudy.objects.filter(orthanc_study_id=orthanc_study_id).first()
    
    @staticmethod
    def get_by_patient_id(patient_id):
        """환자 ID로 Study 조회"""
        return RadiologyStudy.objects.filter(patient_id=patient_id).select_related('order')
    
    @staticmethod
    @transaction.atomic
    def create(data):
        """새 Study 생성"""
        return RadiologyStudy.objects.create(**data)
    
    @staticmethod
    @transaction.atomic
    def update(study_id, data):
        """Study 업데이트"""
        study = RadiologyStudy.objects.get(study_id=study_id)
        for key, value in data.items():
            setattr(study, key, value)
        study.save()
        return study
    
    @staticmethod
    @transaction.atomic
    def update_or_create_by_orthanc_id(orthanc_study_id, data):
        """Orthanc Study ID로 업데이트 또는 생성"""
        study, created = RadiologyStudy.objects.update_or_create(
            orthanc_study_id=orthanc_study_id,
            defaults=data
        )
        return study, created


class RadiologyReportRepository:
    """판독문 Repository"""
    
    @staticmethod
    def get_all():
        """모든 판독문 조회"""
        return RadiologyReport.objects.select_related('study', 'radiologist').all()
    
    @staticmethod
    def get_by_id(report_id):
        """ID로 판독문 조회"""
        return RadiologyReport.objects.select_related('study', 'radiologist').get(report_id=report_id)
    
    @staticmethod
    def get_by_study_id(study_id):
        """Study ID로 판독문 조회"""
        return RadiologyReport.objects.filter(study_id=study_id).select_related('radiologist').first()
    
    @staticmethod
    def get_by_radiologist(radiologist_id):
        """판독의사로 조회"""
        return RadiologyReport.objects.filter(radiologist_id=radiologist_id).select_related('study')
    
    @staticmethod
    @transaction.atomic
    def create(data):
        """새 판독문 생성"""
        return RadiologyReport.objects.create(**data)
    
    @staticmethod
    @transaction.atomic
    def update(report_id, data):
        """판독문 업데이트"""
        report = RadiologyReport.objects.get(report_id=report_id)
        for key, value in data.items():
            setattr(report, key, value)
        report.save()
        return report
    
    @staticmethod
    @transaction.atomic
    def delete(report_id):
        """판독문 삭제"""
        report = RadiologyReport.objects.get(report_id=report_id)
        report.delete()
