"""
CDSS 데이터베이스 시딩 스크립트
- 7개 역할별 사용자 3명씩 생성 (총 21명)
- 환자 30명 생성 (OpenEMR ID 매핑)
- 진료기록(Encounter) 및 처방(Order) 생성
"""

import os
import sys
import random
import uuid
import django
from datetime import datetime, timedelta

# Django 환경 설정 (Standalone 실행을 위해 추가)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()

from django.utils import timezone
from acct.models import User
from emr.models import PatientCache, Encounter, Order, OrderItem

# 한국 이름 데이터
LAST_NAMES = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '한', '오', '서', '신', '권', '황', '안', '송', '전', '홍']
FIRST_NAMES = ['민준', '서준', '도윤', '예준', '시우', '하준', '지호', '지유', '서윤', '서연', '민서', '지우', '하은', '예은', '수아', '지아', '서현', '소율', '하율', '우진']

DEPARTMENTS = ['신경외과', '영상의학과', '진단검사의학과', '내과', '응급의학과']

def generate_korean_name():
    return random.choice(LAST_NAMES) + random.choice(FIRST_NAMES)

def create_users():
    print("🚀 사용자 생성 시작...")
    roles = [
        ('admin', 'Administrator', '행정팀'),
        ('doctor', 'Doctor', '신경외과'),
        ('rib', 'Radiologist', '영상의학과'),
        ('lab', 'Laboratory Technician', '진단검사의학과'),
        ('nurse', 'Nurse', '간호부'),
        ('patient', 'Patient', ''),
        ('external', 'External Organization', '협력기관'),
    ]
    
    created_count = 0
    
    for role, role_display, dept in roles:
        for i in range(1, 4):  # 1~3번
            username = f"{role}{i}"
            email = f"{role}{i}@hospital.com"
            if role == 'patient':
                email = f"patient{i}@example.com"
            
            user_data = {
                'username': username,
                'email': email,
                'role': role,
                'full_name': f"{role_display}_{i}" if role != 'patient' else generate_korean_name(),
                'department': dept,
                'is_active': True,
            }
            
            # 관리자 권한
            if role == 'admin':
                user_data['is_staff'] = True
                user_data['is_superuser'] = True
                
            if User.objects.filter(username=username).exists():
                print(f"  - 사용자 {username} 이미 존재 (Skip)")
                continue
                
            user = User.objects.create_user(**user_data)
            user.set_password(f"{role}123!")
            user.save()
            created_count += 1
            print(f"  - 생성됨: {username} ({role})")
            
    print(f"✅ 총 {created_count}명의 사용자 생성 완료.\n")

def create_patients_and_clinical_data():
    print("🚀 환자 및 임상 데이터 생성 시작...")
    
    # 의사 계정 가져오기 (처방용)
    doctors = list(User.objects.filter(role='doctor'))
    if not doctors:
        print("❌ 의사 계정이 없습니다. 사용자 생성을 먼저 확인하세요.")
        return

    created_patients = 0
    
    for i in range(1, 31):  # 30명
        p_idx = i
        patient_id = f"P-2025-{p_idx:03d}"
        openemr_id = f"PID_{p_idx}"
        
        # 환자 생성
        name = generate_korean_name()
        
        patient, created = PatientCache.objects.get_or_create(
            patient_id=patient_id,
            defaults={
                'family_name': name[0],
                'given_name': name[1:],
                'birth_date': timezone.now().date() - timedelta(days=random.randint(365*20, 365*80)),
                'gender': random.choice(['male', 'female']),
                'phone': f"010-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
                'email': f"patient_{p_idx}@example.com",
                'address': "서울시 강남구 테헤란로 123",
                'openemr_patient_id': openemr_id,
                'blood_type': random.choice(['A+', 'B+', 'O+', 'AB+', 'A-', 'B-']),
                'allergies': random.choice([[], [], ['Penicillin'], ['Peanuts'], ['Dust']]),
            }
        )
        
        if created:
            created_patients += 1
            
        # 진료기록(Encounter) 생성 (1~3건)
        for e_idx in range(1, random.randint(2, 4)):
            enc_date = timezone.now() - timedelta(days=random.randint(1, 100))
            enc_id = f"E-2025-{p_idx:03d}-{e_idx:02d}"
            doctor = random.choice(doctors)
            
            encounter, _ = Encounter.objects.get_or_create(
                encounter_id=enc_id,
                defaults={
                    'patient': patient,
                    'doctor_id': str(doctor.user_id),
                    'encounter_type': 'outpatient',
                    'department': '신경외과',
                    'status': 'completed',
                    'encounter_date': enc_date,
                    'diagnosis': '상세불명의 두통',
                    'chief_complaint': '일주일 전부터 머리가 아파요',
                }
            )
            
            # 처방(Order) 생성 (1~2건)
            if random.random() > 0.3: # 70% 확률로 처방 있음
                order_id = f"O-2025-{p_idx:03d}-{e_idx:02d}"
                order, _ = Order.objects.get_or_create(
                    order_id=order_id,
                    defaults={
                        'patient': patient,
                        'encounter': encounter,
                        'ordered_by': str(doctor.user_id),
                        'order_type': 'medication',
                        'status': 'entered',
                        'urgency': 'routine',
                        'ordered_at': enc_date,
                    }
                )
                
                # 처방 항목
                OrderItem.objects.get_or_create(
                    item_id=f"OI-{order_id}-01",
                    defaults={
                        'order': order,
                        'drug_name': 'Tylenol 500mg',
                        'dosage': '1 tab',
                        'frequency': 'TID',
                        'duration': '3 days',
                        'route': 'PO',
                    }
                )

    print(f"✅ 총 {created_patients}명의 환자 및 관련 임상 데이터 생성 완료.")

if __name__ == '__main__':
    create_users()
    create_patients_and_clinical_data()
