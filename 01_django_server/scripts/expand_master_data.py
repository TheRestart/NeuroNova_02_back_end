import os
import sys
import django
from pathlib import Path

# Django 환경 설정
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()

from ocs.models import MedicationMaster
from lis.models import LabTestMaster

# --- 1. 약물 마스터 데이터 (21종) ---
medications = [
    {"drug_code": "641501710", "drug_name": "아스피린정100mg", "generic_name": "Aspirin", "dosage_form": "정제", "strength": "100mg", "unit": "정", "manufacturer": "바이엘코리아"},
    {"drug_code": "641504990", "drug_name": "타이레놀정500mg", "generic_name": "Acetaminophen", "dosage_form": "정제", "strength": "500mg", "unit": "정", "manufacturer": "한국얀센"},
    {"drug_code": "641505000", "drug_name": "아리셉트정5mg", "generic_name": "Donepezil", "dosage_form": "정제", "strength": "5mg", "unit": "정", "manufacturer": "한국에사이"},
    {"drug_code": "641505010", "drug_name": "아리셉트정10mg", "generic_name": "Donepezil", "dosage_form": "정제", "strength": "10mg", "unit": "정", "manufacturer": "한국에사이"},
    {"drug_code": "642102120", "drug_name": "노바스크정5mg", "generic_name": "Amlodipine", "dosage_form": "정제", "strength": "5mg", "unit": "정", "manufacturer": "한국화이자"},
    {"drug_code": "642100010", "drug_name": "시네메트정", "generic_name": "Levodopa/Carbidopa", "dosage_form": "정제", "strength": "250/25mg", "unit": "정", "manufacturer": "오가논"},
    {"drug_code": "642100020", "drug_name": "덱사메타손정", "generic_name": "Dexamethasone", "dosage_form": "정제", "strength": "0.5mg", "unit": "정", "manufacturer": "유한양행"},
    {"drug_code": "642100030", "drug_name": "만니톨주사액20%", "generic_name": "Mannitol", "dosage_form": "주사제", "strength": "20%", "unit": "bag", "manufacturer": "대한약품"},
    {"drug_code": "642100040", "drug_name": "딜란틴캡슐100mg", "generic_name": "Phenytoin", "dosage_form": "캡슐", "strength": "100mg", "unit": "캡슐", "manufacturer": "한국화이자"},
    {"drug_code": "642100050", "drug_name": "데파코트정500mg", "generic_name": "Valproic Acid", "dosage_form": "정제", "strength": "500mg", "unit": "정", "manufacturer": "한국애보트"},
    {"drug_code": "642100060", "drug_name": "뉴런틴캡슐300mg", "generic_name": "Gabapentin", "dosage_form": "캡슐", "strength": "300mg", "unit": "캡슐", "manufacturer": "한국비엠에스"},
    {"drug_code": "642100070", "drug_name": "에빅사정10mg", "generic_name": "Memantine", "dosage_form": "정제", "strength": "10mg", "unit": "정", "manufacturer": "한국룬드벡"},
    {"drug_code": "642100080", "drug_name": "엑셀론캡슐1.5mg", "generic_name": "Rivastigmine", "dosage_form": "캡슐", "strength": "1.5mg", "unit": "캡슐", "manufacturer": "노바티스"},
    {"drug_code": "642100090", "drug_name": "마오비정", "generic_name": "Selegiline", "dosage_form": "정제", "strength": "5mg", "unit": "정", "manufacturer": "부광약품"},
    {"drug_code": "642100100", "drug_name": "리루텍정", "generic_name": "Riluzole", "dosage_form": "정제", "strength": "50mg", "unit": "정", "manufacturer": "사노피아벤티스"},
    {"drug_code": "642100110", "drug_name": "리피토정20mg", "generic_name": "Atorvastatin", "dosage_form": "정제", "strength": "20mg", "unit": "정", "manufacturer": "한국비엠에스"},
    {"drug_code": "642100120", "drug_name": "쿠마딘정5mg", "generic_name": "Warfarin", "dosage_form": "정제", "strength": "5mg", "unit": "정", "manufacturer": "대화제약"},
    {"drug_code": "642100130", "drug_name": "플라빅스정75mg", "generic_name": "Clopidogrel", "dosage_form": "정제", "strength": "75mg", "unit": "정", "manufacturer": "사노피아벤티스"},
    {"drug_code": "642100140", "drug_name": "액티라제주사", "generic_name": "Alteplase", "dosage_form": "주사제", "strength": "50mg", "unit": "병", "manufacturer": "베링거인겔하임"},
    {"drug_code": "642100150", "drug_name": "니모탑정", "generic_name": "Nimodipine", "dosage_form": "정제", "strength": "30mg", "unit": "정", "manufacturer": "바이엘코리아"},
    {"drug_code": "642100160", "drug_name": "포폴주사", "generic_name": "Propofol", "dosage_form": "주사제", "strength": "200mg/20ml", "unit": "앰플", "manufacturer": "동국제약"},
]

# --- 2. 검사 마스터 데이터 (11종) ---
lab_tests = [
    {"test_code": "L1001", "test_name": "Hemoglobin", "sample_type": "Blood", "method": "Automated", "unit": "g/dL", "reference_range": "12.0-16.0"},
    {"test_code": "L1002", "test_name": "Glucose (Fasting)", "sample_type": "Blood", "method": "Hexokinase", "unit": "mg/dL", "reference_range": "70-99"},
    {"test_code": "L1003", "test_name": "Creatinine", "sample_type": "Serum", "method": "Jaffe", "unit": "mg/dL", "reference_range": "0.7-1.3"},
    {"test_code": "L1004", "test_name": "Sodium", "sample_type": "Serum", "method": "ISE", "unit": "mmol/L", "reference_range": "135-145"},
    {"test_code": "L1005", "test_name": "HbA1c", "sample_type": "Blood", "method": "HPLC", "unit": "%", "reference_range": "4.0-5.6"},
    {"test_code": "L1006", "test_name": "CSF Protein", "sample_type": "CSF", "method": "Turbidimetric", "unit": "mg/dL", "reference_range": "15-45"},
    {"test_code": "L1007", "test_name": "CSF Glucose", "sample_type": "CSF", "method": "Hexokinase", "unit": "mg/dL", "reference_range": "45-80"},
    {"test_code": "L1008", "test_name": "CSF Cell Count (WBC)", "sample_type": "CSF", "method": "Microscopic", "unit": "/uL", "reference_range": "0-5"},
    {"test_code": "L1009", "test_name": "PT (INR)", "sample_type": "Plasma", "method": "Clotting", "unit": "INR", "reference_range": "0.8-1.2"},
    {"test_code": "L1010", "test_name": "CRP", "sample_type": "Serum", "method": "Immunoturbidimetric", "unit": "mg/dL", "reference_range": "0.0-0.5"},
    {"test_code": "L1011", "test_name": "LDL Cholesterol", "sample_type": "Serum", "method": "Calculated", "unit": "mg/dL", "reference_range": "0-130"},
]

def expand_master_data():
    print("🚀 마스터 데이터 확장 시작...")
    
    # 약물 데이터 업로드
    med_count = 0
    for med in medications:
        obj, created = MedicationMaster.objects.update_or_create(
            drug_code=med['drug_code'],
            defaults=med
        )
        if created: med_count += 1
    print(f"✅ 약물: {len(medications)}개 처리됨 ({med_count}개 신규 추가)")
    
    # 검사 데이터 업로드
    lab_count = 0
    for lab in lab_tests:
        obj, created = LabTestMaster.objects.update_or_create(
            test_code=lab['test_code'],
            defaults=lab
        )
        if created: lab_count += 1
    print(f"✅ 검사: {len(lab_tests)}개 처리됨 ({lab_count}개 신규 추가)")

if __name__ == "__main__":
    expand_master_data()
