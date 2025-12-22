"""
EMR 모델 정의

Django MySQL에 저장되는 환자 기본 정보 (캐시)
상세 정보는 OpenEMR에 저장되고 FHIR를 통해 동기화
"""

from django.db import models
from django.utils import timezone
import uuid


class PatientCache(models.Model):
    """
    환자 기본 정보 캐시 테이블

    - Django MySQL에 일반 정보 저장
    - OpenEMR에 상세 정보 저장
    - FHIR API를 통해 양방향 동기화
    """
    GENDER_CHOICES = [
        ('male', '남성'),
        ('female', '여성'),
        ('other', '기타'),
        ('unknown', '미상'),
    ]

    patient_id = models.CharField(
        max_length=20,
        primary_key=True,
        help_text="환자 ID (예: P-2024-001234)"
    )
    family_name = models.CharField(max_length=50, help_text="성")
    given_name = models.CharField(max_length=50, help_text="이름")
    birth_date = models.DateField(help_text="생년월일")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, help_text="성별")
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="전화번호")
    email = models.EmailField(max_length=100, blank=True, null=True, help_text="이메일")
    address = models.TextField(blank=True, null=True, help_text="주소")

    # JSON 필드
    emergency_contact = models.JSONField(
        blank=True,
        null=True,
        help_text="응급 연락처 정보 {'name': '...', 'relationship': '...', 'phone': '...'}"
    )
    allergies = models.JSONField(
        blank=True,
        null=True,
        help_text="알레르기 목록 ['페니실린', '땅콩']"
    )

    blood_type = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        help_text="혈액형 (예: A+, B-, O+, AB-)"
    )

    # OpenEMR 동기화
    openemr_patient_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        help_text="OpenEMR의 환자 ID (FHIR Patient resource ID)"
    )
    last_synced_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="OpenEMR과 마지막 동기화 시간"
    )

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성 시간")
    updated_at = models.DateTimeField(auto_now=True, help_text="수정 시간")

    class Meta:
        db_table = 'emr_patient_cache'
        verbose_name = '환자 캐시'
        verbose_name_plural = '환자 캐시 목록'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['family_name', 'given_name'], name='idx_patient_name'),
            models.Index(fields=['birth_date'], name='idx_patient_birth'),
            models.Index(fields=['phone'], name='idx_patient_phone'),
        ]

    def __str__(self):
        return f"{self.patient_id} - {self.family_name}{self.given_name}"

    @property
    def full_name(self):
        """전체 이름 반환"""
        return f"{self.family_name}{self.given_name}"

    @property
    def is_synced(self):
        """OpenEMR과 동기화 여부"""
        return self.openemr_patient_id is not None


class Encounter(models.Model):
    """
    진료 기록 (Encounter)
    """
    ENCOUNTER_TYPE_CHOICES = [
        ('outpatient', '외래'),
        ('emergency', '응급'),
        ('inpatient', '입원'),
        ('discharge', '퇴원'),
    ]

    STATUS_CHOICES = [
        ('scheduled', '예정'),
        ('in_progress', '진행중'),
        ('completed', '완료'),
        ('cancelled', '취소'),
    ]

    encounter_id = models.CharField(
        max_length=20,
        primary_key=True,
        help_text="진료 ID (예: E-2025-005678)"
    )
    patient = models.ForeignKey(
        PatientCache,
        on_delete=models.CASCADE,
        related_name='encounters',
        db_column='patient_id',
        help_text="환자"
    )
    doctor_id = models.CharField(
        max_length=36,
        help_text="의사 user_id (ACCT_USERS 외래키)"
    )

    encounter_type = models.CharField(
        max_length=20,
        choices=ENCOUNTER_TYPE_CHOICES,
        help_text="진료 유형"
    )
    department = models.CharField(max_length=100, help_text="진료 부서")
    chief_complaint = models.TextField(blank=True, null=True, help_text="주 호소")
    diagnosis = models.TextField(blank=True, null=True, help_text="진단")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        help_text="진료 상태"
    )

    encounter_date = models.DateTimeField(help_text="진료 일시")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'emr_encounters'
        verbose_name = '진료 기록'
        verbose_name_plural = '진료 기록 목록'
        ordering = ['-encounter_date']
        indexes = [
            models.Index(fields=['patient', 'encounter_date'], name='idx_patient_encounter'),
            models.Index(fields=['doctor_id', 'encounter_date'], name='idx_doctor_encounter'),
            models.Index(fields=['status'], name='idx_encounter_status'),
        ]

    def __str__(self):
        return f"{self.encounter_id} - {self.patient.full_name} ({self.encounter_date})"


class Order(models.Model):
    """
    OCS 처방 주문
    """
    ORDER_TYPE_CHOICES = [
        ('medication', '약물'),
        ('lab', '검사'),
        ('radiology', '영상'),
        ('procedure', '시술'),
    ]

    URGENCY_CHOICES = [
        ('routine', '일반'),
        ('urgent', '긴급'),
        ('stat', '즉시'),
    ]

    STATUS_CHOICES = [
        ('pending', '대기'),
        ('approved', '승인'),
        ('in_progress', '진행중'),
        ('completed', '완료'),
        ('cancelled', '취소'),
    ]

    order_id = models.CharField(
        max_length=20,
        primary_key=True,
        help_text="처방 ID (예: O-2025-009876)"
    )
    patient = models.ForeignKey(
        PatientCache,
        on_delete=models.CASCADE,
        related_name='orders',
        db_column='patient_id',
        help_text="환자"
    )
    encounter = models.ForeignKey(
        Encounter,
        on_delete=models.CASCADE,
        related_name='orders',
        db_column='encounter_id',
        blank=True,
        null=True,
        help_text="진료 기록"
    )

    ordered_by = models.CharField(
        max_length=36,
        help_text="처방 의사 user_id"
    )
    order_type = models.CharField(
        max_length=50,
        choices=ORDER_TYPE_CHOICES,
        help_text="처방 유형"
    )
    urgency = models.CharField(
        max_length=20,
        choices=URGENCY_CHOICES,
        default='routine',
        help_text="긴급도"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="처방 상태"
    )
    notes = models.TextField(blank=True, null=True, help_text="처방 메모")

    ordered_at = models.DateTimeField(auto_now_add=True, help_text="처방 시간")
    executed_at = models.DateTimeField(blank=True, null=True, help_text="실행 시간")
    executed_by = models.CharField(
        max_length=36,
        blank=True,
        null=True,
        help_text="실행자 user_id"
    )

    class Meta:
        db_table = 'ocs_orders'
        verbose_name = '처방'
        verbose_name_plural = '처방 목록'
        ordering = ['-ordered_at']
        indexes = [
            models.Index(fields=['patient', 'ordered_at'], name='idx_patient_order'),
            models.Index(fields=['ordered_by', 'ordered_at'], name='idx_doctor_order'),
            models.Index(fields=['status'], name='idx_order_status'),
            models.Index(fields=['order_type'], name='idx_order_type'),
        ]

    def __str__(self):
        return f"{self.order_id} - {self.patient.full_name} ({self.order_type})"


class OrderItem(models.Model):
    """
    처방 항목 (약물 상세)
    """
    item_id = models.CharField(
        max_length=20,
        primary_key=True,
        help_text="처방 항목 ID (예: OI-001)"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        db_column='order_id',
        help_text="처방"
    )

    drug_code = models.CharField(max_length=50, blank=True, null=True, help_text="약물 코드")
    drug_name = models.CharField(max_length=200, help_text="약물명")
    dosage = models.CharField(max_length=50, help_text="용량 (예: 1정)")
    frequency = models.CharField(max_length=50, help_text="횟수 (예: 1일 1회)")
    duration = models.CharField(max_length=20, help_text="기간 (예: 7일)")
    route = models.CharField(max_length=50, help_text="투여 경로 (예: 경구)")
    instructions = models.TextField(blank=True, null=True, help_text="복용 지시사항")

    class Meta:
        db_table = 'ocs_order_items'
        verbose_name = '처방 항목'
        verbose_name_plural = '처방 항목 목록'

    def __str__(self):
        return f"{self.item_id} - {self.drug_name}"
