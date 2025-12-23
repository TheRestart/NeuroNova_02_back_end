"""
Create test users for all 7 roles
"""

from django.core.management.base import BaseCommand
from acct.models import User


class Command(BaseCommand):
    help = 'Create test users for all 7 roles'

    def handle(self, *args, **options):
        # 7 roles test users
        test_users = [
            {
                'username': 'admin1',
                'email': 'admin@hospital.com',
                'password': 'admin123!',
                'role': 'admin',
                'full_name': 'Admin User',
                'department': 'Administration',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'doctor1',
                'email': 'doctor@hospital.com',
                'password': 'doctor123!',
                'role': 'doctor',
                'full_name': 'Dr. Kim',
                'department': 'Neurosurgery',
                'license_number': 'DOC-001',
            },
            {
                'username': 'rib1',
                'email': 'rib@hospital.com',
                'password': 'rib123!',
                'role': 'rib',
                'full_name': 'Dr. Park',
                'department': 'Radiology',
                'license_number': 'RIB-001',
            },
            {
                'username': 'lab1',
                'email': 'lab@hospital.com',
                'password': 'lab123!',
                'role': 'lab',
                'full_name': 'Lee Technician',
                'department': 'Laboratory',
                'license_number': 'LAB-001',
            },
            {
                'username': 'nurse1',
                'email': 'nurse@hospital.com',
                'password': 'nurse123!',
                'role': 'nurse',
                'full_name': 'Nurse Choi',
                'department': 'Nursing',
                'license_number': 'NUR-001',
            },
            {
                'username': 'patient1',
                'email': 'patient@example.com',
                'password': 'patient123!',
                'role': 'patient',
                'full_name': 'Hong Gildong',
                'department': '',
            },
            {
                'username': 'external1',
                'email': 'external@partner.com',
                'password': 'external123!',
                'role': 'external',
                'full_name': 'External Partner',
                'department': 'Partner Organization',
            },
        ]

        created_count = 0
        for user_data in test_users:
            username = user_data['username']

            # Check if user exists
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                self.stdout.write(f"User {username} already exists - UUID: {user.user_id}")
                continue

            # Create user
            password = user_data.pop('password')
            user = User.objects.create_user(**user_data)
            user.set_password(password)
            user.save()

            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f"Created user: {user.username} ({user.role}) - UUID: {user.user_id}")
            )

        self.stdout.write(
            self.style.SUCCESS(f"\nTotal {created_count} users created!")
        )

        # Print doctor UUID for testing
        doctor = User.objects.filter(role='doctor').first()
        if doctor:
            self.stdout.write(
                self.style.WARNING(f"\nDoctor UUID for testing: {doctor.user_id}")
            )
