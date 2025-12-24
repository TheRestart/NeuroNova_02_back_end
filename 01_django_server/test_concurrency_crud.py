
import os
import django
import threading
import time
import requests
import uuid
import json

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()

from emr.models import PatientCache, Order
from emr.services import PatientService, OrderService
from django.db import transaction

def test_optimistic_locking():
    print("\n--- Testing Optimistic Locking ---")
    # 1. 테스트용 환자 생성
    patient = PatientCache.objects.create(
        patient_id=f"T-OPT-{int(time.time())}",
        family_name="Test",
        given_name="Optimistic",
        birth_date="1990-01-01",
        gender="male",
        version=1
    )
    print(f"Created patient: {patient.patient_id}, Version: {patient.version}")

    # 2. 두 개의 스레드에서 동시에 업데이트 시도
    def update_task(patient_id, new_email, version, results):
        try:
            PatientService.update_patient(patient_id, {'email': new_email, 'version': version})
            results.append(True)
        except Exception as e:
            print(f"Update failed as expected: {str(e)}")
            results.append(False)

    results = []
    t1 = threading.Thread(target=update_task, args=(patient.patient_id, "user1@example.com", patient.version, results))
    t2 = threading.Thread(target=update_task, args=(patient.patient_id, "user2@example.com", patient.version, results))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # 3. 결과 확인: 하나는 성공, 하나는 실패해야 함
    success_count = results.count(True)
    fail_count = results.count(False)
    print(f"Success: {success_count}, Fail: {fail_count}")
    
    final_patient = PatientCache.objects.get(patient_id=patient.patient_id)
    print(f"Final Version: {final_patient.version}, Email: {final_patient.email}")
    
    assert success_count == 1
    assert fail_count == 1
    print("Optimistic Locking Test Passed!")

def test_idempotency():
    print("\n--- Testing Idempotency Middleware ---")
    # API 서버가 실행 중이어야 함 (localhost:8000 가정)
    base_url = "http://localhost:8000/api/emr/patients/"
    idempotency_key = str(uuid.uuid4())
    
    payload = {
        "family_name": "Test",
        "given_name": f"Idempotent-{int(time.time())}",
        "birth_date": "1990-01-01",
        "gender": "male",
        "phone": "010-1234-5678"
    }
    
    headers = {
        "X-Idempotency-Key": idempotency_key,
        "Content-Type": "application/json"
    }

    # 1. 첫 번째 요청
    print("Sending first request...")
    response1 = requests.post(base_url, data=json.dumps(payload), headers=headers)
    print(f"Response 1 Status: {response1.status_code}")
    data1 = response1.json()
    patient_id = data1.get('patient_id')

    # 2. 두 번째 요청 (동일한 키)
    print("Sending second request with same key...")
    response2 = requests.post(base_url, data=json.dumps(payload), headers=headers)
    print(f"Response 2 Status: {response2.status_code}")
    data2 = response2.json()

    # 3. 결과 비교
    assert response1.status_code == 201
    assert response2.status_code == 201  # 미들웨어가 201을 캐시해서 반환해야 함
    assert data1['patient_id'] == data2['patient_id']
    print(f"Both requests returned same Patient ID: {patient_id}")
    print("Idempotency Test Passed!")

if __name__ == "__main__":
    try:
        test_optimistic_locking()
        # Idempotency 테스트는 서버가 떠있어야 하므로 주의 (여기서는 로직 확인 위주)
        # test_idempotency() 
    except Exception as e:
        print(f"Test failed: {str(e)}")
