import os
import sys
import django
from pathlib import Path
from datetime import datetime

# Django 환경 설정
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()

from emr.models import PatientCache, Encounter, Order, OrderItem
from emr.services import PatientService, OrderService
from lis.models import LabResult, LabTestMaster
from lis.services import LabResultService
from acct.models import Alert, User
from audit.models import AuditLog
from unittest.mock import patch

def verify_week5():
    print("--- Week 5 Integration Verification Start ---")
    
    # 0. 테스트용 사용자 확인 (의사)
    try:
        doctor = User.objects.get(username='dr.test')
    except User.DoesNotExist:
        doctor = User.objects.create_user(
            username='dr.test', 
            email='test@hosp.com', 
            password='password123',
            role='doctor', 
            full_name='Test Doctor'
        )
    
    # 1. 환자 생성 및 감사 로그 확인
    print("\n[1] Patient Creation & Audit Log")
    patient_data = {
        "family_name": "Test", "given_name": "Patient", 
        "birth_date": "1985-05-05", "gender": "male"
    }
    # OpenEMR 연동 부분은 Mocking
    with patch('emr.services.OpenEMRPatientRepository.create_patient_in_openemr', return_value='1001'):
        result = PatientService.create_patient(patient_data)
        patient, _ = result
    
    if patient:
        print(f"SUCCESS: Patient created: {patient.patient_id}")
        # 감사 로그 확인
        last_audit = AuditLog.objects.filter(model_name='PatientCache', object_id=patient.patient_id).first()
        if last_audit:
            print(f"SUCCESS: Audit log recorded: {last_audit.change_summary}")
        else:
            print("FAILURE: Audit log missing")
    else:
        print("FAILURE: Patient creation returned None")

    # 2. 검사 처방 생성 (OCS)
    print("\n[2] Lab Order Creation (OCS) & Master Data Validation")
    order_data = {
        "patient": patient.patient_id if patient else "P-ERROR",
        "order_type": "lab",
        "urgency": "routine",
        "ordered_by": str(doctor.user_id),
        "notes": "Lipid panel test"
    }
    items_data = [
        {"test_code": "L1001", "dosage": "1", "frequency": "once", "duration": "1d"}, # Hemoglobin
        {"test_code": "L1011", "dosage": "1", "frequency": "once", "duration": "1d"}, # LDL Cholesterol
    ]
    
    with patch('emr.services.OpenEMROrderRepository.create_prescription_in_openemr', return_value=True):
        order, _ = OrderService.create_order(order_data, items_data)
    
    if order:
        print(f"SUCCESS: Order created: {order.order_id}, Items: {order.items.count()}")
        for item in order.items.all():
            print(f"   - {item.drug_name} ({item.drug_code})")
    else:
        print("FAILURE: Order creation failed")

    # 3. 검사 결과 등록 및 이상치 알림 (LIS -> ALERT)
    print("\n[3] Lab Result Entry (LIS) & Abnormal Alert (ALERT)")
    # LDL Cholesterol (L1011) 결과 등록 (정상 범위 0-130인데 200 입력)
    test_master = LabTestMaster.objects.get(test_code='L1011')
    result_data = {
        "order": order,
        "patient": patient,
        "test_master": test_master,
        "result_value": "200",
        "result_unit": "mg/dL",
        "reported_by": str(doctor.user_id),
        "results": {"LDL": 200, "Method": "Calculated", "Warning": "High Cholesterol"}
    }
    
    with patch('acct.services.AlertService._broadcast_to_websocket'):
        lab_result = LabResultService.create_lab_result(result_data)
    
    if lab_result:
        print(f"SUCCESS: Lab result created: {lab_result.result_id}, Abnormal: {lab_result.is_abnormal}")
        print(f"SUCCESS: JSON details saved: {lab_result.result_details}")

        # 알림 확인
        alert = Alert.objects.filter(metadata__result_id=lab_result.result_id).first()
        if alert:
            print(f"SUCCESS: Alert created: {alert.message}")
        else:
            print("FAILURE: Alert missing")
    else:
        print("FAILURE: Lab result creation failed")

    # 4. 감사 로그 전수 검증
    print("\n[4] Audit Log Summary")
    logs = AuditLog.objects.filter(created_at__gte=datetime.now().replace(hour=0, minute=0, second=0))
    print(f"Total Audit Logs today: {logs.count()}")
    for log in logs[:5]:
        print(f"   - [{log.action}] {log.app_label}.{log.model_name}: {log.change_summary}")

    print("\n--- Week 5 Verification Completed ---")

if __name__ == "__main__":
    verify_week5()
