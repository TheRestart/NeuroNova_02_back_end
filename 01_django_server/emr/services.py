
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
        환자 생성 (Parallel Dual-Write)
        - Django DB (cdss_db)와 OpenEMR DB (emr_db)에 독립적으로 요청 전달
        - 각 저장소의 결과를 취합하여 반환
        """
        year = datetime.now().year
        last_number = PatientRepository.get_max_patient_sequence(year)
        new_number = last_number + 1

        patient_id = f'P-{year}-{new_number:06d}'
        data['patient_id'] = patient_id

        persistence_status = {
            "openemr_patient_data": "대기",
            "django_emr_patient_cache": "대기"
        }

        # 1. OpenEMR DB 저장 시도
        openemr_pid = None
        try:
            openemr_pid = OpenEMRPatientRepository.create_patient_in_openemr(data)
            persistence_status["openemr_patient_data"] = "성공"
        except Exception as e:
            persistence_status["openemr_patient_data"] = f"실패: {str(e)}"

        # 2. Django DB 저장 시도
        patient = None
        try:
            if openemr_pid:
                data['openemr_patient_id'] = str(openemr_pid)
            
            patient = PatientRepository.create_patient(data)
            persistence_status["django_emr_patient_cache"] = "성공"
        except Exception as e:
            persistence_status["django_emr_patient_cache"] = f"실패: {str(e)}"

        # 만약 둘 다 실패했다면 예외 던짐
        if persistence_status["openemr_patient_data"] != "성공" and persistence_status["django_emr_patient_cache"] != "성공":
            raise Exception("모든 데이터베이스 저장에 실패했습니다.")

        return patient, persistence_status

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
        진료 기록 생성 (Parallel Dual-Write)
        - Django DB와 OpenEMR DB에 병렬적으로(독립적으로) 데이터 전달
        """
        from ocs.models import DiagnosisMaster
        from .models import EncounterDiagnosis
        from .repositories import OpenEMREncounterRepository

        year = datetime.now().year
        last_number = EncounterRepository.get_max_encounter_sequence(year)
        new_number = last_number + 1

        encounter_id = f'E-{year}-{new_number:06d}'
        data['encounter_id'] = encounter_id

        # 진단 데이터 추출
        diagnosis_items = data.pop('diagnoses', [])

        persistence_status = {
            "openemr_encounters,openemr_forms": "대기",
            "django_emr_encounters,django_emr_encounter_diagnoses": "대기"
        }

        # 1. OpenEMR DB 저장 시도
        try:
            emr_data = data.copy()
            emr_data['diagnoses'] = diagnosis_items
            OpenEMREncounterRepository.create_encounter_in_openemr(emr_data)
            persistence_status["openemr_encounters,openemr_forms"] = "성공"
        except Exception as e:
            persistence_status["openemr_encounters,openemr_forms"] = f"실패: {str(e)}"

        # 2. Django DB 저장 시도
        encounter = None
        try:
            with transaction.atomic():
                encounter = EncounterRepository.create_encounter(data)
                for idx, diag_item in enumerate(diagnosis_items, 1):
                    diag_code = diag_item.get('diag_code')
                    comments = diag_item.get('comments', '')
                    if diag_code:
                        try:
                            master = DiagnosisMaster.objects.get(diag_code=diag_code)
                            EncounterDiagnosis.objects.create(
                                encounter=encounter,
                                diag_code=diag_code,
                                diagnosis_name=master.name_ko,
                                priority=idx,
                                comments=comments
                            )
                        except DiagnosisMaster.DoesNotExist:
                            EncounterDiagnosis.objects.create(
                                encounter=encounter,
                                diag_code=diag_code,
                                diagnosis_name="Unknown Diagnosis",
                                priority=idx,
                                comments=comments
                            )
            persistence_status["django_emr_encounters,django_emr_encounter_diagnoses"] = "성공"
        except Exception as e:
            persistence_status["django_emr_encounters,django_emr_encounter_diagnoses"] = f"실패: {str(e)}"

        if persistence_status["openemr_encounters,openemr_forms"] != "성공" and persistence_status["django_emr_encounters,django_emr_encounter_diagnoses"] != "성공":
            raise Exception("모든 데이터베이스 저장에 실패했습니다.")

        return encounter, persistence_status


class OrderService:
    """처방 비즈니스 로직"""

    @staticmethod
    def create_order(order_data, items_data):
        """
        처방 생성 (Parallel Dual-Write)
        - Django DB와 OpenEMR DB에 독립적으로 요청 전달
        """
        from ocs.models import MedicationMaster

        year = datetime.now().year
        last_number = OrderRepository.get_max_order_sequence(year)
        new_number = last_number + 1

        order_id = f'O-{year}-{new_number:06d}'
        order_data['order_id'] = order_id

        # 항목 ID 생성 및 유효성 검사
        final_items_data = []
        for idx, item in enumerate(items_data, 1):
            drug_code = item.get('drug_code')
            if drug_code:
                try:
                    master = MedicationMaster.objects.get(drug_code=drug_code)
                    item['drug_name'] = master.drug_name
                except MedicationMaster.DoesNotExist:
                    raise Exception(f"유효하지 않은 약물 코드입니다: {drug_code}")

            item_id = f'OI-{order_id}-{idx:03d}'
            item['item_id'] = item_id
            final_items_data.append(item)

        persistence_status = {
            "openemr_prescriptions": "대기",
            "django_emr_orders,django_emr_order_items": "대기"
        }

        # 1. OpenEMR DB 처방 생성 시도
        try:
            OpenEMROrderRepository.create_prescription_in_openemr(order_data, final_items_data)
            persistence_status["openemr_prescriptions"] = "성공"
        except Exception as e:
            persistence_status["openemr_prescriptions"] = f"실패: {str(e)}"

        # 2. Django DB 처방 생성 시도
        order = None
        try:
            order = OrderRepository.create_order(order_data, final_items_data)
            persistence_status["django_emr_orders,django_emr_order_items"] = "성공"
        except Exception as e:
            persistence_status["django_emr_orders,django_emr_order_items"] = f"실패: {str(e)}"

        if not any(v == "성공" for v in persistence_status.values()):
            raise Exception("모든 데이터베이스 저장에 실패했습니다.")

        return order, persistence_status

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
