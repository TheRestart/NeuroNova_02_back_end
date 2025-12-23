import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()

print(f"ENABLE_SECURITY: {settings.ENABLE_SECURITY}")
