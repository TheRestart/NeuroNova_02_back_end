from django.db import models
from emr.models import Order, PatientCache

class LabTestMaster(models.Model):
    """
    임상병리 검사 마스터 데이터 (LOINC 등)
    """
    test_code = models.CharField(max_length=50, primary_key=True, help_text="검사 코드 (LOINC/자체코드)")
    test_name = models.CharField(max_length=255, help_text="검사명")
    sample_type = models.CharField(max_length=100, blank=True, null=True, help_text="검체 유형 (예: Blood, Urine)")
    method = models.CharField(max_length=100, blank=True, null=True, help_text="검사 방법")
    unit = models.CharField(max_length=50, blank=True, null=True, help_text="검사 단위 (예: mg/dL, g/L)")
    reference_range = models.CharField(max_length=255, blank=True, null=True, help_text="참고치 범위 (예: 70-110)")
    
    is_active = models.BooleanField(default=True, help_text="사용 여부")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lis_lab_test_master'
        verbose_name = '검사 마스터'
        verbose_name_plural = '검사 마스터 목록'

    def __str__(self):
        return f"[{self.test_code}] {self.test_name}"


class LabResult(models.Model):
    """
    임상병리 검사 결과
    """
    result_id = models.CharField(max_length=20, primary_key=True, help_text="결과 ID (예: LR-2025-000001)")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='lab_results', help_text="연관된 처방")
    patient = models.ForeignKey(PatientCache, on_delete=models.CASCADE, related_name='lab_results', help_text="환자")
    
    test_master = models.ForeignKey(LabTestMaster, on_delete=models.PROTECT, help_text="검사 마스터 정보")
    
    result_value = models.CharField(max_length=100, help_text="검사 결과값 (수치 또는 텍스트)")
    result_unit = models.CharField(max_length=50, blank=True, null=True, help_text="결과 단위")
    
    is_abnormal = models.BooleanField(default=False, help_text="이상치 여부")
    abnormal_flag = models.CharField(max_length=10, blank=True, null=True, help_text="이상치 플래그 (H: High, L: Low, etc.)")
    
    reported_at = models.DateTimeField(auto_now_add=True, help_text="보고 일시")
    reported_by = models.CharField(max_length=36, help_text="보고자 user_id")
    
    version = models.IntegerField(default=1, help_text="낙관적 락을 위한 버전 필드")

    class Meta:
        db_table = 'lis_lab_results'
        verbose_name = '검사 결과'
        verbose_name_plural = '검사 결과 목록'
        ordering = ['-reported_at']

    def __str__(self):
        return f"{self.result_id} - {self.test_master.test_name}: {self.result_value}"
