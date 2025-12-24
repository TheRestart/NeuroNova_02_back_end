import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()
from emr.models import PatientCache
try:
    p = PatientCache.objects.create(
        patient_id='P-9999-999999',
        family_name='Test',
        given_name='Man',
        birth_date='1900-01-01',
        gender='male'
    )
    print(f"Success! Created patient: {p.patient_id}")
    p.delete()
except Exception as e:
    print(f"Error: {e}")
