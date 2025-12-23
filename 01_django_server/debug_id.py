
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()

from emr.models import PatientCache
from emr.repositories import PatientRepository
from datetime import datetime

def check_patients():
    print("Checking PatientCache...")
    year = datetime.now().year
    
    # 1. Total count
    count = PatientCache.objects.count()
    print(f"Total patients: {count}")
    
    # 2. Get last patient via Repository
    last_repo = PatientRepository.get_last_patient_by_year(year)
    print(f"Repo last patient: {last_repo.patient_id if last_repo else 'None'}")
    
    # 3. List top 5 IDs (descending)
    print("Top 5 IDs in DB:")
    recent = PatientCache.objects.order_by('-patient_id')[:5]
    for p in recent:
        print(f" - {p.patient_id}")
        
    # 4. Check for 'P-2025-000031' specifically
    exists_31 = PatientCache.objects.filter(patient_id=f'P-{year}-000031').exists()
    print(f"Does P-{year}-000031 exist? {exists_31}")

if __name__ == "__main__":
    check_patients()
