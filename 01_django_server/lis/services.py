import logging
import re
from datetime import datetime
from django.db import transaction
from django.db.models import F
from .models import LabResult, LabTestMaster

logger = logging.getLogger(__name__)

class LabResultService:
    """임상병리 결과 비즈니스 로직"""

    @staticmethod
    def create_lab_result(data):
        """
        검사 결과 등록 및 이상치 자동 판정
        """
        order = data.get('order')
        test_master = data.get('test_master')
        result_value = data.get('result_value')
        result_unit = data.get('result_unit')
        
        # 1. ID 자동 생성 (LR-YYYY-NNNNNN)
        year = datetime.now().year
        # 간단하게 카운트로 생성 (실제 운영시는 전용 시퀀스 테이블 권장)
        last_count = LabResult.objects.filter(result_id__startswith=f'LR-{year}-').count()
        result_id = f'LR-{year}-{(last_count + 1):06d}'
        data['result_id'] = result_id

        # 2. 이상치 판정 로직
        is_abnormal = False
        abnormal_flag = None
        
        try:
            # 마스터 데이터의 참고치(reference_range) 가져오기
            ref_range = test_master.reference_range
            if ref_range and result_value:
                # 숫자형 결과값인 경우 범위 비교 시도 (예: "70-110")
                match = re.search(r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)', ref_range)
                if match:
                    low = float(match.group(1))
                    high = float(match.group(2))
                    
                    try:
                        val = float(result_value)
                        if val < low:
                            is_abnormal = True
                            abnormal_flag = 'L'
                        elif val > high:
                            is_abnormal = True
                            abnormal_flag = 'H'
                    except ValueError:
                        # 숫자가 아닌 경우 텍스트 기반 판정 (구현 생략 - 필요시 확장)
                        pass
        except Exception as e:
            logger.error(f"Error during abnormal value detection: {str(e)}")

        data['is_abnormal'] = is_abnormal
        data['abnormal_flag'] = abnormal_flag

        # 3. 상세 결과가 있으면 result_details에 저장 (데이터 보존)
        if 'results' in data and not data.get('result_details'):
            data['result_details'] = data.pop('results')

        try:
            with transaction.atomic():
                # 결과 생성
                result = LabResult.objects.create(**data)
                
                # 이상치인 경우 알림 서비스 트리거 (UC07 연동)
                if is_abnormal:
                    from acct.services import AlertService
                    logger.warning(f"Abnormal lab result detected: {result_id} ({abnormal_flag})")
                    
                    # 담당 의사(order.ordered_by)에게 알림 발송
                    AlertService.send_alert(
                        user_id=order.ordered_by,
                        message=f"이상 검사 결과 감지: {test_master.test_name} ({result_value} {result_unit or ''}) [Flag: {abnormal_flag}]",
                        alert_type='CRITICAL',
                        metadata={
                            'result_id': result_id,
                            'patient_id': order.patient_id,
                            'order_id': order.order_id
                        }
                    )
                
                # [UC09] 감사 로그
                from audit.services import AuditService
                AuditService.log_action(
                    user=None,
                    action='CREATE',
                    app_label='lis',
                    model_name='LabResult',
                    object_id=result_id,
                    change_summary=f"검사 결과 등록: {test_master.test_name} ({result_value})",
                    current_data=data
                )
                
                return result

        except Exception as e:
            logger.error(f"Failed to create lab result: {str(e)}")
            raise e

    @staticmethod
    def get_patient_lab_history(patient_id):
        """환자의 과거 검사 이력 조회"""
        return LabResult.objects.filter(patient_id=patient_id).select_related('test_master')
