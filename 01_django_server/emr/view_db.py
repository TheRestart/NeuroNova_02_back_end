"""
EMR 데이터베이스 조회 스크립트

사용법:
    python emr/view_db.py
"""

import os
import sys
import django
from pathlib import Path

# Django 설정
if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    sys.path.append(str(BASE_DIR))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
    django.setup()

from emr.models import PatientCache, Encounter, Order, OrderItem
from django.db.models import Count, Q


def show_database_summary():
    """데이터베이스 요약 정보"""
    print("\n" + "=" * 80)
    print("  EMR 데이터베이스 요약")
    print("=" * 80)

    patient_count = PatientCache.objects.count()
    encounter_count = Encounter.objects.count()
    order_count = Order.objects.count()
    order_item_count = OrderItem.objects.count()

    print(f"\n📊 테이블별 레코드 수:")
    print(f"   - 환자 (PatientCache): {patient_count}명")
    print(f"   - 진료 기록 (Encounter): {encounter_count}건")
    print(f"   - 처방 (Order): {order_count}건")
    print(f"   - 처방 항목 (OrderItem): {order_item_count}건")

    # OpenEMR 동기화 통계
    synced_patients = PatientCache.objects.filter(openemr_patient_id__isnull=False).count()
    print(f"\n🔄 OpenEMR 동기화 통계:")
    print(f"   - 동기화된 환자: {synced_patients}명")
    print(f"   - 미동기화 환자: {patient_count - synced_patients}명")

    print("=" * 80)


def show_patients(limit=10):
    """환자 목록 조회"""
    patients = PatientCache.objects.all().order_by('-created_at')[:limit]

    if not patients:
        print("\n⚠️  저장된 환자 데이터가 없습니다.")
        return

    print(f"\n📋 최근 환자 목록 (최대 {limit}명):")
    print("=" * 120)
    print(f"{'ID':13s} | {'이름':12s} | {'성별':6s} | {'생년월일':12s} | {'혈액형':6s} | {'전화번호':15s} | {'생성일':20s}")
    print("-" * 120)

    for patient in patients:
        created_at = patient.created_at.strftime('%Y-%m-%d %H:%M:%S') if patient.created_at else 'N/A'
        print(f"{patient.patient_id:13s} | {patient.full_name:12s} | "
              f"{patient.get_gender_display():6s} | {patient.birth_date} | "
              f"{patient.blood_type or 'N/A':6s} | {patient.phone or 'N/A':15s} | {created_at}")

    print("=" * 120)


def show_patient_detail(patient_id):
    """특정 환자 상세 정보 조회"""
    try:
        patient = PatientCache.objects.get(patient_id=patient_id)
    except PatientCache.DoesNotExist:
        print(f"\n❌ 환자 ID '{patient_id}'를 찾을 수 없습니다.")
        return

    print("\n" + "=" * 80)
    print(f"  환자 상세 정보: {patient.full_name}")
    print("=" * 80)

    print(f"\n📋 기본 정보:")
    print(f"   - 환자 ID: {patient.patient_id}")
    print(f"   - 이름: {patient.full_name} ({patient.family_name} {patient.given_name})")
    print(f"   - 성별: {patient.get_gender_display()}")
    print(f"   - 생년월일: {patient.birth_date}")
    print(f"   - 혈액형: {patient.blood_type or 'N/A'}")

    print(f"\n📞 연락처 정보:")
    print(f"   - 전화번호: {patient.phone or 'N/A'}")
    print(f"   - 이메일: {patient.email or 'N/A'}")
    print(f"   - 주소: {patient.address or 'N/A'}")

    if patient.emergency_contact:
        print(f"\n🚨 응급 연락처:")
        print(f"   - 이름: {patient.emergency_contact.get('name', 'N/A')}")
        print(f"   - 관계: {patient.emergency_contact.get('relationship', 'N/A')}")
        print(f"   - 전화번호: {patient.emergency_contact.get('phone', 'N/A')}")

    if patient.allergies:
        print(f"\n⚠️  알레르기:")
        for allergy in patient.allergies:
            print(f"   - {allergy}")
    else:
        print(f"\n⚠️  알레르기: 없음")

    print(f"\n🔄 OpenEMR 동기화:")
    print(f"   - OpenEMR ID: {patient.openemr_patient_id or 'N/A'}")
    print(f"   - 동기화 상태: {'✅ 동기화됨' if patient.is_synced else '❌ 미동기화'}")
    if patient.last_synced_at:
        print(f"   - 마지막 동기화: {patient.last_synced_at.strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n📅 시스템 정보:")
    print(f"   - 생성일: {patient.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   - 수정일: {patient.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")

    # 진료 기록 조회
    encounters = patient.encounters.all()[:5]
    if encounters:
        print(f"\n🏥 진료 기록 (최근 5건):")
        for enc in encounters:
            print(f"   - {enc.encounter_id} | {enc.encounter_type} | {enc.status} | {enc.encounter_date}")

    # 처방 조회
    orders = patient.orders.all()[:5]
    if orders:
        print(f"\n💊 처방 기록 (최근 5건):")
        for order in orders:
            print(f"   - {order.order_id} | {order.order_type} | {order.status} | {order.ordered_at}")

    print("=" * 80)


def show_encounters(limit=10):
    """진료 기록 목록"""
    encounters = Encounter.objects.select_related('patient').order_by('-encounter_date')[:limit]

    if not encounters:
        print("\n⚠️  저장된 진료 기록이 없습니다.")
        return

    print(f"\n🏥 최근 진료 기록 (최대 {limit}건):")
    print("=" * 100)
    print(f"{'진료ID':15s} | {'환자':12s} | {'진료유형':10s} | {'상태':10s} | {'진료일시':20s}")
    print("-" * 100)

    for enc in encounters:
        enc_date = enc.encounter_date.strftime('%Y-%m-%d %H:%M:%S')
        print(f"{enc.encounter_id:15s} | {enc.patient.full_name:12s} | "
              f"{enc.get_encounter_type_display():10s} | {enc.get_status_display():10s} | {enc_date}")

    print("=" * 100)


def show_orders(limit=10):
    """처방 목록"""
    orders = Order.objects.select_related('patient').order_by('-ordered_at')[:limit]

    if not orders:
        print("\n⚠️  저장된 처방이 없습니다.")
        return

    print(f"\n💊 최근 처방 (최대 {limit}건):")
    print("=" * 110)
    print(f"{'처방ID':15s} | {'환자':12s} | {'처방유형':10s} | {'긴급도':8s} | {'상태':10s} | {'처방일시':20s}")
    print("-" * 110)

    for order in orders:
        ordered_at = order.ordered_at.strftime('%Y-%m-%d %H:%M:%S')
        print(f"{order.order_id:15s} | {order.patient.full_name:12s} | "
              f"{order.get_order_type_display():10s} | {order.get_urgency_display():8s} | "
              f"{order.get_status_display():10s} | {ordered_at}")

    print("=" * 110)


def show_statistics():
    """통계 정보"""
    print("\n" + "=" * 80)
    print("  상세 통계")
    print("=" * 80)

    # 성별 통계
    print("\n👥 환자 성별 분포:")
    gender_stats = PatientCache.objects.values('gender').annotate(count=Count('patient_id'))
    for stat in gender_stats:
        gender_display = dict(PatientCache.GENDER_CHOICES).get(stat['gender'], stat['gender'])
        print(f"   - {gender_display}: {stat['count']}명")

    # 혈액형 통계
    print("\n🩸 혈액형 분포:")
    blood_stats = PatientCache.objects.exclude(blood_type__isnull=True).exclude(blood_type='').values('blood_type').annotate(count=Count('patient_id')).order_by('-count')
    for stat in blood_stats:
        print(f"   - {stat['blood_type']}: {stat['count']}명")

    # 진료 유형별 통계
    if Encounter.objects.exists():
        print("\n🏥 진료 유형별 통계:")
        enc_stats = Encounter.objects.values('encounter_type').annotate(count=Count('encounter_id'))
        for stat in enc_stats:
            enc_type = dict(Encounter.ENCOUNTER_TYPE_CHOICES).get(stat['encounter_type'], stat['encounter_type'])
            print(f"   - {enc_type}: {stat['count']}건")

    # 처방 유형별 통계
    if Order.objects.exists():
        print("\n💊 처방 유형별 통계:")
        order_stats = Order.objects.values('order_type').annotate(count=Count('order_id'))
        for stat in order_stats:
            order_type = dict(Order.ORDER_TYPE_CHOICES).get(stat['order_type'], stat['order_type'])
            print(f"   - {order_type}: {stat['count']}건")

    print("=" * 80)


def search_patients(keyword):
    """환자 검색"""
    patients = PatientCache.objects.filter(
        Q(patient_id__icontains=keyword) |
        Q(family_name__icontains=keyword) |
        Q(given_name__icontains=keyword) |
        Q(phone__icontains=keyword) |
        Q(email__icontains=keyword)
    )

    if not patients:
        print(f"\n⚠️  검색 결과가 없습니다: '{keyword}'")
        return

    print(f"\n🔍 검색 결과 ({patients.count()}건):")
    print("=" * 100)
    print(f"{'ID':13s} | {'이름':12s} | {'성별':6s} | {'생년월일':12s} | {'전화번호':15s}")
    print("-" * 100)

    for patient in patients:
        print(f"{patient.patient_id:13s} | {patient.full_name:12s} | "
              f"{patient.get_gender_display():6s} | {patient.birth_date} | {patient.phone or 'N/A':15s}")

    print("=" * 100)


def export_to_csv():
    """환자 데이터를 CSV로 내보내기"""
    import csv
    from datetime import datetime

    filename = f"patients_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    patients = PatientCache.objects.all()

    if not patients:
        print("\n⚠️  내보낼 데이터가 없습니다.")
        return

    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['patient_id', 'family_name', 'given_name', 'birth_date', 'gender',
                      'phone', 'email', 'address', 'blood_type', 'created_at']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for patient in patients:
            writer.writerow({
                'patient_id': patient.patient_id,
                'family_name': patient.family_name,
                'given_name': patient.given_name,
                'birth_date': patient.birth_date,
                'gender': patient.gender,
                'phone': patient.phone or '',
                'email': patient.email or '',
                'address': patient.address or '',
                'blood_type': patient.blood_type or '',
                'created_at': patient.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

    print(f"\n✅ CSV 파일로 내보내기 완료: {filename}")
    print(f"   총 {patients.count()}명의 환자 데이터가 저장되었습니다.")


if __name__ == "__main__":
    while True:
        print("\n" + "=" * 80)
        print("  EMR 데이터베이스 조회 도구")
        print("=" * 80)
        print("\n1. 데이터베이스 요약")
        print("2. 환자 목록 조회")
        print("3. 환자 상세 정보 (ID 입력)")
        print("4. 진료 기록 조회")
        print("5. 처방 조회")
        print("6. 통계 정보")
        print("7. 환자 검색")
        print("8. CSV 내보내기")
        print("0. 종료")

        choice = input("\n선택하세요 (0-8): ").strip()

        if choice == '1':
            show_database_summary()
        elif choice == '2':
            limit = input("조회할 환자 수 (기본값 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            show_patients(limit)
        elif choice == '3':
            patient_id = input("환자 ID를 입력하세요 (예: P-2025-001): ").strip()
            if patient_id:
                show_patient_detail(patient_id)
        elif choice == '4':
            limit = input("조회할 진료 기록 수 (기본값 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            show_encounters(limit)
        elif choice == '5':
            limit = input("조회할 처방 수 (기본값 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            show_orders(limit)
        elif choice == '6':
            show_statistics()
        elif choice == '7':
            keyword = input("검색어를 입력하세요 (이름, ID, 전화번호 등): ").strip()
            if keyword:
                search_patients(keyword)
        elif choice == '8':
            export_to_csv()
        elif choice == '0':
            print("\n👋 종료합니다.")
            break
        else:
            print("\n❌ 잘못된 선택입니다.")

        input("\nEnter를 눌러 계속...")
