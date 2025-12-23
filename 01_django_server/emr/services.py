
from datetime import datetime
from django.db import transaction
from .repositories import (
    PatientRepository,
    EncounterRepository,
    OrderRepository,
    EncounterRepository,
    OrderRepository,
    OpenEMRPatientRepository,
    OpenEMROrderRepository
)
import logging

logger = logging.getLogger(__name__)


class PatientService:
    """환자 비즈니스 로직"""

    @staticmethod
    def create_patient(data):
        """
        환자 생성 및 ID 자동 생성 (P-YYYY-NNNNNN)
        - Django DB (cdss_db)의 emr_patient_cache 테이블에 등록
        - OpenEMR DB (emr_db)의 patient_data 테이블에 동시 등록
        """
        year = datetime.now().year
        # [Fix] ID 포맷 불일치(3자리 vs 6자리)로 인한 중복 오류 해결을 위해 Max Sequence 직접 조회
        last_number = PatientRepository.get_max_patient_sequence(year)
        new_number = last_number + 1

        patient_id = f'P-{year}-{new_number:06d}'
        data['patient_id'] = patient_id

        # Transaction으로 Django DB와 OpenEMR DB 동시 등록 보장
        try:
            with transaction.atomic():
                # 1. OpenEMR DB에 환자 등록
                openemr_pid = OpenEMRPatientRepository.create_patient_in_openemr(data)
                logger.info(f"Patient created in OpenEMR DB: pid={openemr_pid}, pubpid={patient_id}")

                # 2. Django DB에 환자 등록 (Cache)
                # OpenEMR pid를 포함하여 저장
                data['openemr_patient_id'] = str(openemr_pid)
                patient = PatientRepository.create_patient(data)
                logger.info(f"Patient created (cached) in Django DB: {patient_id}")

                return patient

        except Exception as e:
            logger.error(f"Failed to create patient in dual databases: {str(e)}")
            raise Exception(f"환자 등록 실패 (Django + OpenEMR): {str(e)}")


class EncounterService:
    """진료 기록 비즈니스 로직"""

    @staticmethod
    def create_encounter(data):
        """
        진료 기록 생성 및 ID 자동 생성 (E-YYYY-NNNNNN)
        """
        year = datetime.now().year
        last_number = EncounterRepository.get_max_encounter_sequence(year)
        new_number = last_number + 1

        encounter_id = f'E-{year}-{new_number:06d}'
        data['encounter_id'] = encounter_id

        return EncounterRepository.create_encounter(data)


class OrderService:
    """처방 비즈니스 로직"""

    @staticmethod
    def create_order(order_data, items_data):
        """
        처방 생성 및 ID 자동 생성 (O-YYYY-NNNNNN)
        처방 항목 ID 자동 생성 (OI-ORDERID-NNN)
        """
        year = datetime.now().year
        last_number = OrderRepository.get_max_order_sequence(year)
        new_number = last_number + 1

        order_id = f'O-{year}-{new_number:06d}'
        order_data['order_id'] = order_id

        # 항목 ID 생성 정책 적용
        final_items_data = []
        for idx, item in enumerate(items_data, 1):
            item_id = f'OI-{order_id}-{idx:03d}'
            item['item_id'] = item_id
            final_items_data.append(item)

        # 1. OpenEMR DB에 처방 생성 (Source of Truth)
        try:
            OpenEMROrderRepository.create_prescription_in_openemr(order_data, final_items_data)
            logger.info(f"Prescription created in OpenEMR for Order {order_id}")
        except Exception as e:
            logger.error(f"Failed to create prescription in OpenEMR: {str(e)}")
            raise Exception(f"OpenEMR 처방 생성 실패: {str(e)}")

        # 2. Django DB에 처방 생성 (Cache) (Transaction)
        order = OrderRepository.create_order(order_data, final_items_data)
        logger.info(f"Prescription created (cached) in Django DB: {order_id}")

        return order
