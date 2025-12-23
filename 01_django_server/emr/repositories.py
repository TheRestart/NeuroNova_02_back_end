
from django.db import transaction, connections
from datetime import datetime
from .models import PatientCache, Encounter, Order, OrderItem


class OpenEMRPatientRepository:
    """OpenEMR patient_data 테이블 직접 접근"""

    @staticmethod
    def create_patient_in_openemr(data):
        """
        OpenEMR patient_data 테이블에 환자 등록 (Manual PID Increment)

        Args:
            data: PatientCache 모델에서 변환된 환자 데이터

        Returns:
            생성된 OpenEMR pid (int)
        """
        with connections['openemr'].cursor() as cursor:
            # 1. Manual PID Generation
            # OpenEMR의 pid 컬럼이 AI(Auto Increment)가 아닐 수 있으므로 직접 MAX값 조회
            cursor.execute("SELECT MAX(pid) FROM patient_data")
            row = cursor.fetchone()
            current_max_pid = row[0] if row and row[0] is not None else 0
            new_pid = current_max_pid + 1

            # 2. 필수 필드 매핑 (Django PatientCache -> OpenEMR patient_data)
            # id 컬럼도 pid와 동일하게 맞춰주는 것이 안전함 (OpenEMR 스키마에 따라 id가 PK일 수 있음)
            sql = """
                INSERT INTO patient_data (
                    id, pid, pubpid,
                    fname, lname, mname, DOB, sex,
                    street, city, state, postal_code, country_code,
                    phone_home, phone_cell, email,
                    regdate, last_updated,
                    title, language, financial, status,
                    hipaa_mail, hipaa_voice, hipaa_notice, hipaa_message,
                    hipaa_allowsms, hipaa_allowemail,
                    allow_patient_portal, dupscore
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s
                )
            """

            # 주소 파싱 (address 필드를 street, city, state로 분리)
            address_parts = data.get('address', '').split(',')
            street = address_parts[0].strip() if len(address_parts) > 0 else ''
            city = address_parts[1].strip() if len(address_parts) > 1 else ''
            state = address_parts[2].strip() if len(address_parts) > 2 else ''

            # 성별 변환 (male/female -> Male/Female)
            sex = data.get('gender', 'male').capitalize()

            # 현재 시간
            now = datetime.now()

            params = (
                # id, pid, pubpid (Django patient_id)
                new_pid, 
                new_pid, 
                data.get('patient_id', ''),

                # fname, lname, mname, DOB, sex
                data.get('given_name', ''),
                data.get('family_name', ''),
                '',  # middle name
                data.get('birth_date'),
                sex,

                # street, city, state, postal_code, country_code
                street,
                city,
                state,
                '',  # postal_code
                'KR',  # country_code (대한민국)

                # phone_home, phone_cell, email
                data.get('phone', ''),
                data.get('phone', ''),  # cell phone도 동일하게
                data.get('email', ''),

                # regdate, last_updated
                now,
                now,

                # title, language, financial, status
                '',  # title
                'korean',  # language
                '',  # financial
                'active',  # status

                # HIPAA 기본값들
                'YES',  # hipaa_mail
                'YES',  # hipaa_voice
                'YES',  # hipaa_notice
                '',  # hipaa_message
                'YES',  # hipaa_allowsms
                'YES',  # hipaa_allowemail

                # allow_patient_portal, dupscore
                'YES',  # allow_patient_portal
                -9,  # dupscore (기본값)
            )

            cursor.execute(sql, params)

            # 생성된 pid 반환
            return new_pid

    @staticmethod
    def get_patient_by_pubpid(pubpid):
        """
        pubpid로 OpenEMR 환자 조회

        Args:
            pubpid: Django patient_id (P-YYYY-NNNNNN)

        Returns:
            환자 정보 dict 또는 None
        """
        with connections['openemr'].cursor() as cursor:
            sql = """
                SELECT pid, fname, lname, DOB, sex, email, phone_home, pubpid
                FROM patient_data
                WHERE pubpid = %s
            """
            cursor.execute(sql, [pubpid])
            row = cursor.fetchone()

            if row:
                return {
                    'pid': row[0],
                    'fname': row[1],
                    'lname': row[2],
                    'DOB': row[3],
                    'sex': row[4],
                    'email': row[5],
                    'phone_home': row[6],
                    'pubpid': row[7],
                }
            return None


class PatientRepository:
    """환자 데이터 저장소"""

    @staticmethod
    def create_patient(data):
        """환자 생성"""
        return PatientCache.objects.create(**data)

    @staticmethod
    def get_patient_by_id(patient_id):
        """환자 조회"""
        return PatientCache.objects.filter(patient_id=patient_id).first()

    @staticmethod
    def get_last_patient_by_year(year):
        """해당 연도의 마지막 환자 조회 (Deprecated: String Sort Issue)"""
        return PatientCache.objects.filter(
            patient_id__startswith=f'P-{year}-'
        ).order_by('-patient_id').first()

    @staticmethod
    def get_max_patient_sequence(year):
        """
        해당 연도의 가장 큰 시퀀스 번호 반환 (포맷 혼용 대응)
        예: P-2025-030 (3자리) vs P-2025-000031 (6자리) 문자열 정렬 문제 해결
        """
        prefix = f'P-{year}-'
        # 모든 ID를 가져와서 숫자 부분만 파싱하여 최대값 계산 (데이터량이 많지 않다고 가정)
        patients = PatientCache.objects.filter(patient_id__startswith=prefix).values_list('patient_id', flat=True)
        
        max_seq = 0
        for pid in patients:
            try:
                parts = pid.split('-')
                if len(parts) >= 3:
                    seq = int(parts[-1])
                    if seq > max_seq:
                        max_seq = seq
            except ValueError:
                continue
                
        return max_seq


class EncounterRepository:
    """진료 기록 데이터 저장소"""

    @staticmethod
    def create_encounter(data):
        """진료 기록 생성"""
        return Encounter.objects.create(**data)

    @staticmethod
    def get_encounter_by_id(encounter_id):
        """진료 기록 조회"""
        return Encounter.objects.filter(encounter_id=encounter_id).first()

    @staticmethod
    def get_last_encounter_by_year(year):
        """해당 연도의 마지막 진료 기록 조회 (ID 생성용)"""
        return Encounter.objects.filter(
            encounter_id__startswith=f'E-{year}-'
        ).order_by('-encounter_id').first()


class OrderRepository:
    """처방 데이터 저장소"""

    @staticmethod
    def create_order(order_data, items_data):
        """처방 및 처방 항목 생성 (Transaction 보장)"""
        with transaction.atomic():
            order = Order.objects.create(**order_data)

            for item_datum in items_data:
                OrderItem.objects.create(order=order, **item_datum)

            return order

    @staticmethod
    def get_last_order_by_year(year):
        """해당 연도의 마지막 처방 조회 (ID 생성용)"""
        return Order.objects.filter(
            order_id__startswith=f'O-{year}-'
        ).order_by('-order_id').first()
