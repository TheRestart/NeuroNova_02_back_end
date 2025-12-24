from django.db import models

class MedicationMaster(models.Model):
    """
    약물 마스터 데이터 (KDC, EDI 코드 등)
    """
    drug_code = models.CharField(max_length=50, primary_key=True, help_text="약물 표준 코드 (KDC/EDI)")
    drug_name = models.CharField(max_length=255, help_text="약물명 (상품명)")
    generic_name = models.CharField(max_length=255, blank=True, null=True, help_text="성분명 (일반명)")
    dosage_form = models.CharField(max_length=100, blank=True, null=True, help_text="제형 (예: 정제, 주사제)")
    strength = models.CharField(max_length=100, blank=True, null=True, help_text="함량 (예: 500mg)")
    unit = models.CharField(max_length=50, blank=True, null=True, help_text="단위 (예: 정, 바이알)")
    manufacturer = models.CharField(max_length=255, blank=True, null=True, help_text="제조사/수입사")
    
    is_active = models.BooleanField(default=True, help_text="사용 여부")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ocs_medication_master'
        verbose_name = '약물 마스터'
        verbose_name_plural = '약물 마스터 목록'

    def __str__(self):
        return f"[{self.drug_code}] {self.drug_name}"


class DiagnosisMaster(models.Model):
    """
    질병/진단 마스터 데이터 (ICD-10, KCD)
    """
    diag_code = models.CharField(max_length=20, primary_key=True, help_text="질병 코드 (ICD-10/KCD)")
    name_ko = models.CharField(max_length=255, help_text="질병명 (한글)")
    name_en = models.CharField(max_length=255, blank=True, null=True, help_text="질병명 (영문)")
    category = models.CharField(max_length=100, blank=True, null=True, help_text="분류 (대분류)")
    
    is_active = models.BooleanField(default=True, help_text="사용 여부")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ocs_diagnosis_master'
        verbose_name = '진단 마스터'
        verbose_name_plural = '진단 마스터 목록'

    def __str__(self):
        return f"[{self.diag_code}] {self.name_ko}"
