"""
테스트 사용자 생성 스크립트
7개 역할별로 1명씩 생성
"""

from acct.models import User

# 기존 사용자 삭제 (선택)
# User.objects.all().delete()

# 7개 역할별 테스트 사용자 생성
test_users = [
    {
        'username': 'admin1',
        'email': 'admin@hospital.com',
        'password': 'admin123!',
        'role': 'admin',
        'full_name': '관리자',
        'department': '행정팀',
        'is_staff': True,
        'is_superuser': True,
    },
    {
        'username': 'doctor1',
        'email': 'doctor@hospital.com',
        'password': 'doctor123!',
        'role': 'doctor',
        'full_name': '김의사',
        'department': '신경외과',
        'license_number': 'DOC-001',
    },
    {
        'username': 'rib1',
        'email': 'rib@hospital.com',
        'password': 'rib123!',
        'role': 'rib',
        'full_name': '박방사선',
        'department': '영상의학과',
        'license_number': 'RIB-001',
    },
    {
        'username': 'lab1',
        'email': 'lab@hospital.com',
        'password': 'lab123!',
        'role': 'lab',
        'full_name': '이검사',
        'department': '진단검사의학과',
        'license_number': 'LAB-001',
    },
    {
        'username': 'nurse1',
        'email': 'nurse@hospital.com',
        'password': 'nurse123!',
        'role': 'nurse',
        'full_name': '최간호사',
        'department': '간호부',
        'license_number': 'NUR-001',
    },
    {
        'username': 'patient1',
        'email': 'patient@example.com',
        'password': 'patient123!',
        'role': 'patient',
        'full_name': '홍길동',
        'department': '',
    },
    {
        'username': 'external1',
        'email': 'external@partner.com',
        'password': 'external123!',
        'role': 'external',
        'full_name': '외부기관',
        'department': '협력기관',
    },
]

created_users = []

for user_data in test_users:
    # 이미 존재하는지 확인
    if User.objects.filter(username=user_data['username']).exists():
        print(f"⏭️  사용자 {user_data['username']} 이미 존재")
        user = User.objects.get(username=user_data['username'])
        created_users.append(user)
        continue

    # 비밀번호 분리
    password = user_data.pop('password')

    # 사용자 생성
    user = User.objects.create_user(**user_data)
    user.set_password(password)
    user.save()

    created_users.append(user)
    print(f"✅ 사용자 생성: {user.username} ({user.role}) - UUID: {user.user_id}")

print(f"\n총 {len(created_users)}명의 사용자 준비 완료!")
print("\n📋 사용자 목록:")
for user in created_users:
    print(f"  - {user.username} ({user.role}): {user.user_id}")

# 의사 UUID 출력 (처방 생성 시 사용)
doctor = User.objects.filter(role='doctor').first()
if doctor:
    print(f"\n💊 처방 생성 시 사용할 의사 UUID: {doctor.user_id}")
