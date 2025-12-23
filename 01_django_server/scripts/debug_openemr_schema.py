"""
OpenEMR DB 스키마 디버깅 스크립트
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()

from django.db import connections

def inspect_schema():
    print("🔍 OpenEMR 스키마 확인...")
    tables = ['patient_data', 'form_encounter', 'prescriptions']
    
    with connections['openemr'].cursor() as cursor:
        for table in tables:
            print(f"\n======== {table} ========")
            try:
                cursor.execute(f"SHOW CREATE TABLE {table}")
                row = cursor.fetchone()
                print(row[1])
            except Exception as e:
                print(f"Error: {e}")

if __name__ == '__main__':
    inspect_schema()
