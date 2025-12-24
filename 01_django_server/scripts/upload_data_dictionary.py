import os
import sys
import csv
import django
from pathlib import Path

# Django 환경 설정
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()

from ocs.models import MedicationMaster, DiagnosisMaster
from lis.models import LabTestMaster

def upload_medications(csv_file):
    print(f"🚀 약물 데이터 업로드 시작: {csv_file}")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        meds = []
        for row in reader:
            meds.append(MedicationMaster(
                drug_code=row['drug_code'],
                drug_name=row['drug_name'],
                generic_name=row.get('generic_name', ''),
                dosage_form=row.get('dosage_form', ''),
                strength=row.get('strength', ''),
                unit=row.get('unit', ''),
                manufacturer=row.get('manufacturer', '')
            ))
        
        MedicationMaster.objects.bulk_create(meds, ignore_conflicts=True)
    print(f"✅ {len(meds)}개의 약물 데이터 처리 완료.")

def upload_diagnoses(csv_file):
    print(f"🚀 진단 데이터 업로드 시작: {csv_file}")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        diags = []
        for row in reader:
            diags.append(DiagnosisMaster(
                diag_code=row['diag_code'],
                name_ko=row['name_ko'],
                name_en=row.get('name_en', ''),
                category=row.get('category', '')
            ))
        
        DiagnosisMaster.objects.bulk_create(diags, ignore_conflicts=True)
    print(f"✅ {len(diags)}개의 진단 데이터 처리 완료.")

def upload_lab_tests(csv_file):
    print(f"🚀 검사 데이터 업로드 시작: {csv_file}")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        tests = []
        for row in reader:
            tests.append(LabTestMaster(
                test_code=row['test_code'],
                test_name=row['test_name'],
                sample_type=row.get('sample_type', ''),
                method=row.get('method', ''),
                unit=row.get('unit', ''),
                reference_range=row.get('reference_range', '')
            ))
        
        LabTestMaster.objects.bulk_create(tests, ignore_conflicts=True)
    print(f"✅ {len(tests)}개의 검사 데이터 처리 완료.")

if __name__ == "__main__":
    # 데이터 디렉토리 생성
    data_dir = BASE_DIR / 'scripts' / 'data'
    data_dir.mkdir(exist_ok=True)
    
    # 1. 시뮬레이션 데이터 생성 (파일이 없을 경우)
    def create_dummy_csv(path, fieldnames, rows):
        if not path.exists():
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"📝 더미 파일 생성됨: {path.name}")

    # 약물 더미
    create_dummy_csv(
        data_dir / 'medications.csv',
        ['drug_code', 'drug_name', 'generic_name', 'dosage_form', 'strength', 'unit', 'manufacturer'],
        [
            {'drug_code': '641501710', 'drug_name': '아스피린정100mg', 'generic_name': 'Aspirin', 'dosage_form': '정제', 'strength': '100mg', 'unit': '정', 'manufacturer': '바이엘코리아'},
            {'drug_code': '641504990', 'drug_name': '타이레놀정500mg', 'generic_name': 'Acetaminophen', 'dosage_form': '정제', 'strength': '500mg', 'unit': '정', 'manufacturer': '한국얀센'},
            {'drug_code': '642102120', 'drug_name': '노바스크정5mg', 'generic_name': 'Amlodipine', 'dosage_form': '정제', 'strength': '5mg', 'unit': '정', 'manufacturer': '한국화이자'},
        ]
    )

    # 진단 더미
    create_dummy_csv(
        data_dir / 'diagnoses.csv',
        ['diag_code', 'name_ko', 'name_en', 'category'],
        [
            {'diag_code': 'I10', 'name_ko': '본태성(원발성) 고혈압', 'name_en': 'Essential (primary) hypertension', 'category': '순환기계'},
            {'diag_code': 'E11', 'name_ko': '2형 당뇨병', 'name_en': 'Type 2 diabetes mellitus', 'category': '내분비계'},
            {'diag_code': 'C71', 'name_ko': '뇌의 악성 신생물', 'name_en': 'Malignant neoplasm of brain', 'category': '신생물'},
        ]
    )

    # 검사 더미
    create_dummy_csv(
        data_dir / 'lab_tests.csv',
        ['test_code', 'test_name', 'sample_type', 'method', 'unit', 'reference_range'],
        [
            {'test_code': 'L1001', 'test_name': 'Hemoglobin', 'sample_type': 'Blood', 'method': 'Automated', 'unit': 'g/dL', 'reference_range': '12.0-16.0'},
            {'test_code': 'L1002', 'test_name': 'Glucose (Fasting)', 'sample_type': 'Blood', 'method': 'Hexokinase', 'unit': 'mg/dL', 'reference_range': '70-99'},
            {'test_code': 'L1003', 'test_name': 'Creatinine', 'sample_type': 'Serum', 'method': 'Jaffe', 'unit': 'mg/dL', 'reference_range': '0.7-1.3'},
        ]
    )

    # 2. 업로드 실행
    upload_medications(data_dir / 'medications.csv')
    upload_diagnoses(data_dir / 'diagnoses.csv')
    upload_lab_tests(data_dir / 'lab_tests.csv')
