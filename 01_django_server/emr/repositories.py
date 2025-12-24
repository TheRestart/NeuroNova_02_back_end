
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
    def get_patient_by_id(patient_id, for_update=False):
        """환자 조회 (for_update 옵션 추가)"""
        queryset = PatientCache.objects.filter(patient_id=patient_id)
        if for_update:
            queryset = queryset.select_for_update()
        return queryset.first()

    @staticmethod
    def update_patient_optimistic(patient_id, old_version, data):
        """낙관적 락을 이용한 환자 정보 업데이트"""
        from django.db.models import F
        rows_updated = PatientCache.objects.filter(
            patient_id=patient_id, 
            version=old_version
        ).update(**data, version=F('version') + 1)
        return rows_updated > 0

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
    def get_encounter_by_id(encounter_id, for_update=False):
        """진료 기록 조회 (for_update 옵션 추가)"""
        queryset = Encounter.objects.filter(encounter_id=encounter_id)
        if for_update:
            queryset = queryset.select_for_update()
        return queryset.first()

    @staticmethod
    def update_encounter_optimistic(encounter_id, old_version, data):
        """낙관적 락을 이용한 진료 기록 업데이트"""
        from django.db.models import F
        rows_updated = Encounter.objects.filter(
            encounter_id=encounter_id, 
            version=old_version
        ).update(**data, version=F('version') + 1)
        return rows_updated > 0

    @staticmethod
    def get_max_encounter_sequence(year):
        """해당 연도 진료기록 Max Sequence 조회"""
        prefix = f'E-{year}-'
        # 모든 ID 조회 후 메모리에서 Max 계산 (데이터량 적음 가정)
        encounters = Encounter.objects.filter(encounter_id__startswith=prefix).values_list('encounter_id', flat=True)
        
        max_seq = 0
        for eid in encounters:
            try:
                parts = eid.split('-')
                if len(parts) >= 3:
                    seq = int(parts[-1])
                    if seq > max_seq:
                        max_seq = seq
            except ValueError:
                continue
        return max_seq


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
    def get_order_by_id(order_id, for_update=False):
        """처방 조회 (for_update 옵션 추가)"""
        queryset = Order.objects.filter(order_id=order_id)
        if for_update:
            queryset = queryset.select_for_update()
        return queryset.first()

    @staticmethod
    def update_order_optimistic(order_id, old_version, data):
        """낙관적 락을 이용한 처방 업데이트"""
        from django.db.models import F
        rows_updated = Order.objects.filter(
            order_id=order_id, 
            version=old_version
        ).update(**data, version=F('version') + 1)
        return rows_updated > 0

    @staticmethod
    def get_max_order_sequence(year):
        """해당 연도 처방 Max Sequence 조회"""
        prefix = f'O-{year}-'
        orders = Order.objects.filter(order_id__startswith=prefix).values_list('order_id', flat=True)
        
        max_seq = 0
        for oid in orders:
            try:
                parts = oid.split('-')
                if len(parts) >= 3:
                    seq = int(parts[-1])
                    if seq > max_seq:
                        max_seq = seq
            except ValueError:
                continue
        return max_seq


class OpenEMROrderRepository:
    """OpenEMR prescriptions 테이블 직접 접근"""

    @staticmethod
    def create_prescription_in_openemr(order_data, items_data):
        """
        OpenEMR prescriptions 테이블에 처방 등록
        
        Args:
            order_data: Order 생성을 위한 딕셔너리 (patient_id 포함 필수)
            items_data: OrderItem 생성을 위한 딕셔너리 리스트
        
        Returns:
            list[int]: 생성된 OpenEMR prescription id 목록 (필요시)
        """
        # 1. 환자의 OpenEMR pid 조회
        # order_data에는 'patient'가 객체일 수도 있고 ID 문자열일 수도 있음
        # 여기서는 patient_id 문자열을 우선 사용
        patient_ref = order_data.get('patient')
        if hasattr(patient_ref, 'patient_id'):
            patient_id_str = patient_ref.patient_id
        else:
            patient_id_str = str(patient_ref)

        patient_info = OpenEMRPatientRepository.get_patient_by_pubpid(patient_id_str)
        if not patient_info:
            raise Exception(f"OpenEMR에서 환자를 찾을 수 없습니다. (Patient ID: {patient_id_str})")
        
        pid = patient_info['pid']
        now = datetime.now()

        created_ids = []

        # 2. 각 처방 항목을 prescriptions 테이블에 Insert
        with connections['openemr'].cursor() as cursor:
            for item in items_data:
                sql = """
                    INSERT INTO prescriptions (
                        patient_id,
                        drug,
                        dosage,
                        quantity,
                        refills,
                        start_date,
                        date_added,
                        date_modified,
                        provider_id,
                        active,
                        txDate,
                        usage_category_title,
                        request_intent_title
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                # item이 객체인지 딕셔너리인지 확인
                drug_name = getattr(item, 'drug_name', item.get('drug_name'))
                dosage = getattr(item, 'dosage', item.get('dosage'))

                # Dosage + Frequency + Duration을 조합하여 quantity나 note에 넣을 수도 있지만,
                # 여기서는 주요 필드만 매핑
                params = (
                    pid,                    # patient_id (int)
                    drug_name,              # drug
                    dosage,                 # dosage
                    1,                      # quantity (기본값)
                    0,                      # refills (기본값)
                    now.date(),             # start_date
                    now,                    # date_added
                    now,                    # date_modified
                    1,                      # provider_id (Default Admin user for now, or fetch map)
                    1,                      # active (1=active)
                    now.date(),             # txDate (처방 일자)
                    '',                     # usage_category_title (필수, 빈값)
                    ''                      # request_intent_title (필수, 빈값)
                )
                
                cursor.execute(sql, params)
                created_ids.append(cursor.lastrowid)

        return created_ids

