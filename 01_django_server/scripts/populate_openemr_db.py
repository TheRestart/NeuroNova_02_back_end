"""
OpenEMR 데이터베이스 시딩 스크립트 (Final)
- Raw SQL 사용
- PID 수동 관리 및 무결성 체크
- Prescriptions 필수 필드 완벽 대응
- form_id 컬럼 제거 (존재하지 않음)
"""

import os
import sys
import random
import django
from datetime import datetime, timedelta

# Django 환경 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()

from django.db import connections

LAST_NAMES = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '한', '오', '서', '신', '권', '황', '안', '송', '전', '홍']
FIRST_NAMES = ['민준', '서준', '도윤', '예준', '시우', '하준', '지호', '지유', '서윤', '서연', '민서', '지우', '하은', '예은', '수아', '지아', '서현', '소율', '하율', '우진']

def generate_korean_name():
    return random.choice(LAST_NAMES), random.choice(FIRST_NAMES)

def populate_openemr():
    print("🚀 OpenEMR 데이터베이스 시딩 시작 (Final)...")
    
    try:
        cursor = connections['openemr'].cursor()
    except Exception as e:
        print(f"❌ OpenEMR 데이터베이스 연결 실패: {e}")
        return

    # 현재 MAX PID 조회
    cursor.execute("SELECT MAX(pid) FROM patient_data")
    row = cursor.fetchone()
    current_max_pid = row[0] if row and row[0] is not None else 0
    print(f"  - 현재 Max PID: {current_max_pid}")

    for i in range(1, 31):  # 30명
        pubpid = f"PID_{i}"
        
        # 존재 여부 확인
        cursor.execute("SELECT pid FROM patient_data WHERE pubpid = %s", [pubpid])
        row = cursor.fetchone()
        
        if row:
            pid = row[0]
            # print(f"    - 환자 존재함: {pubpid} (PID: {pid}) - Skip")
        else:
            current_max_pid += 1
            pid = current_max_pid
            
            lname, fname = generate_korean_name()
            dob = (datetime.now() - timedelta(days=random.randint(365*20, 365*80))).strftime('%Y-%m-%d')
            sex = random.choice(['Male', 'Female'])
            date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                sql = """
                    INSERT INTO patient_data 
                    (id, pid, pubpid, fname, lname, DOB, sex, date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, [pid, pid, pubpid, fname, lname, dob, sex, date_now])
                print(f"    - 환자 생성됨: {pubpid} (PID: {pid})")
            except Exception as e:
                print(f"    ❌ 환자 생성 실패 ({pubpid}): {e}")
                continue

        # 진료기록(form_encounter) 생성
        try:
            cursor.execute("SELECT count(*) FROM form_encounter WHERE pid = %s", [pid])
            encounter_count = cursor.fetchone()[0]
            
            if encounter_count == 0:
                encounter_date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S')
                enc_id = random.randint(10000, 99999) 
                
                sql_enc = """
                    INSERT INTO form_encounter
                    (date, pid, encounter, reason, facility_id)
                    VALUES (%s, %s, %s, %s, 1)
                """
                cursor.execute(sql_enc, [encounter_date, pid, enc_id, "Regular Checkup"])
                print(f"      L 진료기록 생성 (Encounter: {enc_id})")
                
                # 처방(prescriptions) 생성
                if random.random() > 0.5:
                    drug = random.choice(['Tylenol', 'Amoxicillin', 'Ibuprofen', 'Lisinopril'])
                    
                    # form_id 제거
                    sql_rx = """
                        INSERT INTO prescriptions
                        (patient_id, encounter, drug, date_added, active, 
                         txDate, date_modified, drug_id, provider_id, 
                         usage_category_title, quantity)
                        VALUES (%s, %s, %s, %s, 1, 
                                %s, %s, 0, 1, 
                                'Medication', 1)
                    """
                    cursor.execute(sql_rx, [pid, enc_id, drug, encounter_date, 
                                          encounter_date, encounter_date])
                    print(f"      L 처방 생성 ({drug})")
                    
        except Exception as e:
            # 에러가 나도 다음 환자로 진행
            print(f"      ❌ 진료/처방 생성 실패: {e}")

    print("\n✅ OpenEMR 데이터 시딩 완료.")

if __name__ == '__main__':
    populate_openemr()
