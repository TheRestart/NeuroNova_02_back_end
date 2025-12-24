
from datetime import datetime
from django.db import transaction
from .repositories import (
    PatientRepository,
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

    @staticmethod
    def update_patient(patient_id, data, use_pessimistic=True):
        """
        환자 정보 업데이트
        - use_pessimistic: True일 경우 select_for_update() 사용
        - 낙관적 락: 데이터에 포함된 'version'을 기반으로 업데이트 수행
        """
        old_version = data.pop('version', None)
        
        try:
            with transaction.atomic():
                # 1. 비관적 락 (Pessimistic Locking)
                if use_pessimistic:
                    patient = PatientRepository.get_patient_by_id(patient_id, for_update=True)
                    if not patient:
                        raise Exception("환자를 찾을 수 없습니다.")
                
                # 2. 낙관적 락 (Optimistic Locking)
                if old_version is not None:
                    success = PatientRepository.update_patient_optimistic(patient_id, old_version, data)
                    if not success:
                        raise Exception("데이터 충돌이 발생했습니다. (Optimistic Lock Failure)")
                else:
                    # 버전 정보가 없으면 일반 업데이트
                    PatientCache.objects.filter(patient_id=patient_id).update(**data)
                
                return PatientRepository.get_patient_by_id(patient_id)

        except Exception as e:
            logger.error(f"Update failed for patient {patient_id}: {str(e)}")
            raise e


class EncounterService:
    """진료 기록 비즈니스 로직"""

    @staticmethod
    def create_encounter(data):
        """
        진료 기록 생성 및 ID 자동 생성 (E-YYYY-NNNNNN)
        - DiagnosisMaster 연동 및 구조화된 진단 정보 저장
        """
        from ocs.models import DiagnosisMaster
        from .models import EncounterDiagnosis

        year = datetime.now().year
        last_number = EncounterRepository.get_max_encounter_sequence(year)
        new_number = last_number + 1

        encounter_id = f'E-{year}-{new_number:06d}'
        data['encounter_id'] = encounter_id

        # 1. 진단 코드 추출 (데이터에 'diagnosis_codes'가 있다고 가정)
        diagnosis_codes = data.pop('diagnosis_codes', [])

        try:
            with transaction.atomic():
                # 진료 기록 생성
                encounter = EncounterRepository.create_encounter(data)
                
                # 구조화된 진단 정보 저장
                for idx, diag_code in enumerate(diagnosis_codes, 1):
                    try:
                        master = DiagnosisMaster.objects.get(diag_code=diag_code)
                        EncounterDiagnosis.objects.create(
                            encounter=encounter,
                            diag_code=diag_code,
                            diagnosis_name=master.name_ko,
                            priority=idx # 순서대로 주진단(1), 부진단(2...)
                        )
                    except DiagnosisMaster.DoesNotExist:
                        logger.warning(f"Diagnosis code {diag_code} not found in master data.")
                        # 필요 시 예외 발생
                        # raise Exception(f"유효하지 않은 진단 코드입니다: {diag_code}")

                return encounter
        except Exception as e:
            logger.error(f"Failed to create encounter with diagnoses: {str(e)}")
            raise e


class OrderService:
    """처방 비즈니스 로직"""

    @staticmethod
    def create_order(order_data, items_data):
        """
        처방 생성 및 ID 자동 생성 (O-YYYY-NNNNNN)
        처방 항목 ID 자동 생성 (OI-ORDERID-NNN)
        - MedicationMaster 연동 및 유효성 검사 추가
        """
        from ocs.models import MedicationMaster

        year = datetime.now().year
        last_number = OrderRepository.get_max_order_sequence(year)
        new_number = last_number + 1

        order_id = f'O-{year}-{new_number:06d}'
        order_data['order_id'] = order_id

        # 항목 ID 생성 정책 및 유효성 검사 적용
        final_items_data = []
        for idx, item in enumerate(items_data, 1):
            drug_code = item.get('drug_code')
            if drug_code:
                # 1. 마스터 데이터 존재 여부 확인
                try:
                    master = MedicationMaster.objects.get(drug_code=drug_code)
                    # 마스터 데이터에 있는 정보로 이름 보정 (선택 사항)
                    item['drug_name'] = master.drug_name
                except MedicationMaster.DoesNotExist:
                    logger.warning(f"Medication code {drug_code} not found in master data.")
                    # 현업 요구사항에 따라 에러를 던지거나 경고만 남김 (여기서는 예외 발생)
                    raise Exception(f"유효하지 않은 약물 코드입니다: {drug_code}")

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

    @staticmethod
    def execute_order(order_id, executed_by, current_version):
        """
        처방 실행 (상태 업데이트)
        - 비관적 락과 낙관적 락을 합쳐서 적용
        """
        try:
            with transaction.atomic():
                # 1. 비관적 락
                order = OrderRepository.get_order_by_id(order_id, for_update=True)
                if not order:
                    raise Exception("처방을 찾을 수 없습니다.")
                
                # 2. 낙관적 락 적용하며 업데이트
                update_data = {
                    'status': 'completed',
                    'executed_at': datetime.now(),
                    'executed_by': executed_by
                }
                
                success = OrderRepository.update_order_optimistic(order_id, current_version, update_data)
                if not success:
                    raise Exception("다른 사용자에 의해 처방 상태가 이미 변경되었습니다. (Concurrency Error)")
                
                # [UC07] 처방 실행 완료 알림 발송
                try:
                    from acct.services import AlertService
                    AlertService.send_alert(
                        user_id=order.ordered_by, # 처방 의사에게 완료 알림
                        message=f"처방이 실행되었습니다: {order_id}",
                        alert_type='SUCCESS',
                        metadata={'order_id': order_id, 'patient_id': order.patient_id}
                    )
                except Exception as alert_err:
                    logger.warning(f"Failed to send order execution alert: {str(alert_err)}")

                return OrderRepository.get_order_by_id(order_id)
        except Exception as e:
            logger.error(f"Order execution failed: {str(e)}")
            raise e
