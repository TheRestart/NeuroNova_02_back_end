"""
더미 환자 데이터 로딩 스크립트

사용법:
    python manage.py shell < emr/load_dummy_patients.py
    또는
    python emr/load_dummy_patients.py (Django 독립 실행)
"""

import os
import sys
import json
import django
from pathlib import Path

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Django 설정 (독립 실행 시)
if __name__ == "__main__":
    # 프로젝트 루트 경로 설정
    BASE_DIR = Path(__file__).resolve().parent.parent
    sys.path.append(str(BASE_DIR))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
    django.setup()

from emr.models import PatientCache
from datetime import datetime


def load_dummy_patients():
    """더미 환자 데이터를 JSON 파일에서 로드하여 데이터베이스에 저장"""

    # JSON 파일 경로
    current_dir = Path(__file__).resolve().parent
    json_file = current_dir / 'dummy_patients.json'

    if not json_file.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {json_file}")
        return

    # JSON 파일 읽기
    with open(json_file, 'r', encoding='utf-8') as f:
        patients_data = json.load(f)

    print(f"📄 {len(patients_data)}명의 환자 데이터를 로드했습니다.")
    print("=" * 60)

    created_count = 0
    updated_count = 0
    error_count = 0

    for idx, patient_data in enumerate(patients_data, 1):
        try:
            patient_id = patient_data['patient_id']

            # 환자가 이미 존재하는지 확인
            patient, created = PatientCache.objects.update_or_create(
                patient_id=patient_id,
                defaults={
                    'family_name': patient_data['family_name'],
                    'given_name': patient_data['given_name'],
                    'birth_date': patient_data['birth_date'],
                    'gender': patient_data['gender'],
                    'phone': patient_data.get('phone', ''),
                    'email': patient_data.get('email', ''),
                    'address': patient_data.get('address', ''),
                    'emergency_contact': patient_data.get('emergency_contact'),
                    'allergies': patient_data.get('allergies', []),
                    'blood_type': patient_data.get('blood_type', ''),
                }
            )

            if created:
                created_count += 1
                status = "✅ 생성"
            else:
                updated_count += 1
                status = "🔄 업데이트"

            print(f"{idx:2d}. {status} | {patient.patient_id} | {patient.full_name} | {patient.gender} | {patient.birth_date}")

        except Exception as e:
            error_count += 1
            print(f"❌ 오류 [{idx}번 환자]: {e}")

    print("=" * 60)
    print(f"\n📊 결과 요약:")
    print(f"   - 신규 생성: {created_count}명")
    print(f"   - 업데이트: {updated_count}명")
    print(f"   - 오류: {error_count}명")
    print(f"   - 전체: {len(patients_data)}명")
    print(f"\n✨ 데이터 로딩 완료!")

    # 전체 환자 수 확인
    total_patients = PatientCache.objects.count()
    print(f"\n📈 현재 데이터베이스 총 환자 수: {total_patients}명")


def delete_all_patients():
    """모든 환자 데이터 삭제 (주의!)"""
    count = PatientCache.objects.count()
    if count > 0:
        confirm = input(f"⚠️  {count}명의 모든 환자 데이터를 삭제하시겠습니까? (yes/no): ")
        if confirm.lower() == 'yes':
            PatientCache.objects.all().delete()
            print(f"🗑️  {count}명의 환자 데이터를 삭제했습니다.")
        else:
            print("❌ 삭제가 취소되었습니다.")
    else:
        print("ℹ️  삭제할 환자 데이터가 없습니다.")


def show_patients():
    """저장된 환자 목록 출력"""
    patients = PatientCache.objects.all().order_by('patient_id')
    count = patients.count()

    if count == 0:
        print("ℹ️  저장된 환자 데이터가 없습니다.")
        return

    print(f"\n📋 저장된 환자 목록 ({count}명):")
    print("=" * 80)
    print(f"{'No':3s} | {'Patient ID':12s} | {'이름':10s} | {'성별':4s} | {'생년월일':12s} | {'혈액형':6s}")
    print("-" * 80)

    for idx, patient in enumerate(patients, 1):
        print(f"{idx:3d} | {patient.patient_id:12s} | {patient.full_name:10s} | "
              f"{patient.get_gender_display():4s} | {patient.birth_date} | {patient.blood_type or 'N/A':6s}")

    print("=" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  더미 환자 데이터 로딩 스크립트")
    print("=" * 60 + "\n")

    # 메뉴 선택
    print("1. 더미 데이터 로드 (30명)")
    print("2. 환자 목록 조회")
    print("3. 모든 환자 데이터 삭제")
    print("0. 종료")

    choice = input("\n선택하세요 (0-3): ").strip()

    if choice == '1':
        load_dummy_patients()
    elif choice == '2':
        show_patients()
    elif choice == '3':
        delete_all_patients()
    elif choice == '0':
        print("👋 종료합니다.")
    else:
        print("❌ 잘못된 선택입니다.")
