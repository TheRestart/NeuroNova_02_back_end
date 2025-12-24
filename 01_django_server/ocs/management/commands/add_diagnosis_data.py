"""
진단 마스터 데이터 추가 Django Management Command
Usage: python manage.py add_diagnosis_data
"""
from django.core.management.base import BaseCommand
from ocs.models import DiagnosisMaster


class Command(BaseCommand):
    help = '진단 마스터 데이터 추가 (뇌 질환, 호흡계 질환)'

    def handle(self, *args, **options):
        # 진단 마스터 데이터 정의
        diagnosis_data = [
            # === 뇌 질환 (G00-G99: 신경계통의 질환) ===

            # 뇌혈관 질환
            {"diag_code": "I60.0", "name_ko": "비외상성 지주막하출혈", "name_en": "Subarachnoid hemorrhage", "category": "뇌혈관질환"},
            {"diag_code": "I61.0", "name_ko": "뇌내출혈", "name_en": "Intracerebral hemorrhage", "category": "뇌혈관질환"},
            {"diag_code": "I63.0", "name_ko": "뇌경색증", "name_en": "Cerebral infarction", "category": "뇌혈관질환"},
            {"diag_code": "I64", "name_ko": "출혈 또는 경색으로 명시되지 않은 뇌졸중", "name_en": "Stroke, not specified", "category": "뇌혈관질환"},
            {"diag_code": "G45.0", "name_ko": "일과성 뇌허혈발작", "name_en": "Transient cerebral ischemic attack", "category": "뇌혈관질환"},

            # 뇌종양
            {"diag_code": "C71.0", "name_ko": "뇌, 천막상부의 악성 신생물", "name_en": "Malignant neoplasm of brain, supratentorial", "category": "뇌종양"},
            {"diag_code": "C71.1", "name_ko": "전두엽의 악성 신생물", "name_en": "Malignant neoplasm of frontal lobe", "category": "뇌종양"},
            {"diag_code": "C71.2", "name_ko": "측두엽의 악성 신생물", "name_en": "Malignant neoplasm of temporal lobe", "category": "뇌종양"},
            {"diag_code": "C71.3", "name_ko": "두정엽의 악성 신생물", "name_en": "Malignant neoplasm of parietal lobe", "category": "뇌종양"},
            {"diag_code": "C71.4", "name_ko": "후두엽의 악성 신생물", "name_en": "Malignant neoplasm of occipital lobe", "category": "뇌종양"},
            {"diag_code": "C71.5", "name_ko": "뇌실의 악성 신생물", "name_en": "Malignant neoplasm of cerebral ventricle", "category": "뇌종양"},
            {"diag_code": "C71.6", "name_ko": "소뇌의 악성 신생물", "name_en": "Malignant neoplasm of cerebellum", "category": "뇌종양"},
            {"diag_code": "C71.7", "name_ko": "뇌간의 악성 신생물", "name_en": "Malignant neoplasm of brain stem", "category": "뇌종양"},
            {"diag_code": "D33.0", "name_ko": "뇌, 천막상부의 양성 신생물", "name_en": "Benign neoplasm of brain, supratentorial", "category": "뇌종양"},
            {"diag_code": "D33.1", "name_ko": "뇌, 천막하부의 양성 신생물", "name_en": "Benign neoplasm of brain, infratentorial", "category": "뇌종양"},
            {"diag_code": "D33.2", "name_ko": "뇌의 양성 신생물", "name_en": "Benign neoplasm of brain, unspecified", "category": "뇌종양"},

            # 신경계 퇴행성 질환
            {"diag_code": "G20", "name_ko": "파킨슨병", "name_en": "Parkinson disease", "category": "퇴행성뇌질환"},
            {"diag_code": "G30.0", "name_ko": "알츠하이머병", "name_en": "Alzheimer disease", "category": "퇴행성뇌질환"},
            {"diag_code": "G30.1", "name_ko": "조발성 알츠하이머병", "name_en": "Alzheimer disease with early onset", "category": "퇴행성뇌질환"},
            {"diag_code": "G30.9", "name_ko": "상세불명의 알츠하이머병", "name_en": "Alzheimer disease, unspecified", "category": "퇴행성뇌질환"},
            {"diag_code": "G31.0", "name_ko": "국한성 뇌위축", "name_en": "Circumscribed brain atrophy", "category": "퇴행성뇌질환"},
            {"diag_code": "G35", "name_ko": "다발성 경화증", "name_en": "Multiple sclerosis", "category": "탈수초성질환"},

            # 뇌전증
            {"diag_code": "G40.0", "name_ko": "국소발생 관련성 특발성 뇌전증", "name_en": "Localization-related epilepsy", "category": "뇌전증"},
            {"diag_code": "G40.1", "name_ko": "단순부분발작을 동반한 증상성 국소발생 관련성 뇌전증", "name_en": "Localization-related symptomatic epilepsy", "category": "뇌전증"},
            {"diag_code": "G40.3", "name_ko": "전신성 특발성 뇌전증", "name_en": "Generalized idiopathic epilepsy", "category": "뇌전증"},
            {"diag_code": "G40.9", "name_ko": "상세불명의 뇌전증", "name_en": "Epilepsy, unspecified", "category": "뇌전증"},

            # 뇌염/수막염
            {"diag_code": "G03.0", "name_ko": "비화농성 수막염", "name_en": "Nonpyogenic meningitis", "category": "감염성뇌질환"},
            {"diag_code": "G03.9", "name_ko": "상세불명의 수막염", "name_en": "Meningitis, unspecified", "category": "감염성뇌질환"},
            {"diag_code": "G04.0", "name_ko": "급성 파종성 뇌염", "name_en": "Acute disseminated encephalitis", "category": "감염성뇌질환"},
            {"diag_code": "G04.9", "name_ko": "상세불명의 뇌염, 척수염 및 뇌척수염", "name_en": "Encephalitis, unspecified", "category": "감염성뇌질환"},

            # === 호흡계 질환 (J00-J99: 호흡계통의 질환) ===

            # 상기도 감염
            {"diag_code": "J00", "name_ko": "급성 비인두염(감기)", "name_en": "Acute nasopharyngitis (common cold)", "category": "급성상기도감염"},
            {"diag_code": "J01.0", "name_ko": "급성 상악동염", "name_en": "Acute maxillary sinusitis", "category": "급성상기도감염"},
            {"diag_code": "J01.9", "name_ko": "상세불명의 급성 부비동염", "name_en": "Acute sinusitis, unspecified", "category": "급성상기도감염"},
            {"diag_code": "J02.0", "name_ko": "연쇄구균 인두염", "name_en": "Streptococcal pharyngitis", "category": "급성상기도감염"},
            {"diag_code": "J02.9", "name_ko": "상세불명의 급성 인두염", "name_en": "Acute pharyngitis, unspecified", "category": "급성상기도감염"},
            {"diag_code": "J03.0", "name_ko": "연쇄구균 편도염", "name_en": "Streptococcal tonsillitis", "category": "급성상기도감염"},
            {"diag_code": "J03.9", "name_ko": "상세불명의 급성 편도염", "name_en": "Acute tonsillitis, unspecified", "category": "급성상기도감염"},
            {"diag_code": "J04.0", "name_ko": "급성 후두염", "name_en": "Acute laryngitis", "category": "급성상기도감염"},
            {"diag_code": "J06.0", "name_ko": "여러 부위 및 상세불명 부위의 급성 상기도감염", "name_en": "Acute upper respiratory infection", "category": "급성상기도감염"},
            {"diag_code": "J06.9", "name_ko": "상세불명의 급성 상기도감염", "name_en": "Acute upper respiratory infection, unspecified", "category": "급성상기도감염"},

            # 인플루엔자
            {"diag_code": "J10.0", "name_ko": "인플루엔자 바이러스가 확인된 인플루엔자, 폐렴", "name_en": "Influenza with pneumonia", "category": "인플루엔자"},
            {"diag_code": "J10.1", "name_ko": "인플루엔자 바이러스가 확인된 인플루엔자", "name_en": "Influenza with other respiratory manifestations", "category": "인플루엔자"},
            {"diag_code": "J11.0", "name_ko": "인플루엔자 바이러스 미확인, 폐렴", "name_en": "Influenza with pneumonia, virus not identified", "category": "인플루엔자"},
            {"diag_code": "J11.1", "name_ko": "인플루엔자 바이러스 미확인", "name_en": "Influenza, virus not identified", "category": "인플루엔자"},

            # 하기도 감염
            {"diag_code": "J12.0", "name_ko": "아데노바이러스 폐렴", "name_en": "Adenoviral pneumonia", "category": "폐렴"},
            {"diag_code": "J12.9", "name_ko": "상세불명의 바이러스 폐렴", "name_en": "Viral pneumonia, unspecified", "category": "폐렴"},
            {"diag_code": "J13", "name_ko": "폐렴연쇄구균에 의한 폐렴", "name_en": "Pneumonia due to Streptococcus pneumoniae", "category": "폐렴"},
            {"diag_code": "J14", "name_ko": "헤모필루스 인플루엔자균에 의한 폐렴", "name_en": "Pneumonia due to Haemophilus influenzae", "category": "폐렴"},
            {"diag_code": "J15.0", "name_ko": "클렙시엘라 폐렴간균에 의한 폐렴", "name_en": "Pneumonia due to Klebsiella pneumoniae", "category": "폐렴"},
            {"diag_code": "J15.9", "name_ko": "상세불명의 세균성 폐렴", "name_en": "Bacterial pneumonia, unspecified", "category": "폐렴"},
            {"diag_code": "J18.0", "name_ko": "기관지폐렴", "name_en": "Bronchopneumonia", "category": "폐렴"},
            {"diag_code": "J18.1", "name_ko": "대엽성 폐렴", "name_en": "Lobar pneumonia", "category": "폐렴"},
            {"diag_code": "J18.9", "name_ko": "상세불명의 폐렴", "name_en": "Pneumonia, unspecified", "category": "폐렴"},
            {"diag_code": "J20.0", "name_ko": "마이코플라스마 폐렴균에 의한 급성 기관지염", "name_en": "Acute bronchitis due to Mycoplasma pneumoniae", "category": "기관지염"},
            {"diag_code": "J20.9", "name_ko": "상세불명의 급성 기관지염", "name_en": "Acute bronchitis, unspecified", "category": "기관지염"},
            {"diag_code": "J21.0", "name_ko": "호흡기 세포융합 바이러스에 의한 급성 세기관지염", "name_en": "Acute bronchiolitis due to RSV", "category": "기관지염"},
            {"diag_code": "J21.9", "name_ko": "상세불명의 급성 세기관지염", "name_en": "Acute bronchiolitis, unspecified", "category": "기관지염"},

            # 만성 하기도 질환
            {"diag_code": "J40", "name_ko": "급성 또는 만성으로 명시되지 않은 기관지염", "name_en": "Bronchitis, not specified", "category": "만성하기도질환"},
            {"diag_code": "J41.0", "name_ko": "단순 만성 기관지염", "name_en": "Simple chronic bronchitis", "category": "만성하기도질환"},
            {"diag_code": "J42", "name_ko": "상세불명의 만성 기관지염", "name_en": "Chronic bronchitis, unspecified", "category": "만성하기도질환"},
            {"diag_code": "J43.0", "name_ko": "맥클라우드 증후군", "name_en": "MacLeod syndrome", "category": "만성하기도질환"},
            {"diag_code": "J43.9", "name_ko": "상세불명의 폐기종", "name_en": "Emphysema, unspecified", "category": "만성하기도질환"},
            {"diag_code": "J44.0", "name_ko": "급성 하기도감염이 동반된 만성폐쇄성폐질환", "name_en": "COPD with acute lower respiratory infection", "category": "COPD"},
            {"diag_code": "J44.1", "name_ko": "급성 악화가 동반된 만성폐쇄성폐질환", "name_en": "COPD with acute exacerbation", "category": "COPD"},
            {"diag_code": "J44.9", "name_ko": "상세불명의 만성폐쇄성폐질환", "name_en": "COPD, unspecified", "category": "COPD"},

            # 천식
            {"diag_code": "J45.0", "name_ko": "알레르기가 주로 작용하는 천식", "name_en": "Predominantly allergic asthma", "category": "천식"},
            {"diag_code": "J45.1", "name_ko": "비알레르기성 천식", "name_en": "Nonallergic asthma", "category": "천식"},
            {"diag_code": "J45.8", "name_ko": "혼합형 천식", "name_en": "Mixed asthma", "category": "천식"},
            {"diag_code": "J45.9", "name_ko": "상세불명의 천식", "name_en": "Asthma, unspecified", "category": "천식"},

            # 기타 호흡기 질환
            {"diag_code": "J84.0", "name_ko": "폐포성 및 폐포벽 병태", "name_en": "Alveolar and parietoalveolar conditions", "category": "간질성폐질환"},
            {"diag_code": "J84.1", "name_ko": "기타 간질성 폐질환", "name_en": "Other interstitial pulmonary diseases", "category": "간질성폐질환"},
            {"diag_code": "J90", "name_ko": "달리 분류되지 않은 흉수", "name_en": "Pleural effusion", "category": "흉막질환"},
            {"diag_code": "J93.0", "name_ko": "자연기흉", "name_en": "Spontaneous tension pneumothorax", "category": "흉막질환"},
            {"diag_code": "J93.1", "name_ko": "기타 자연기흉", "name_en": "Other spontaneous pneumothorax", "category": "흉막질환"},
            {"diag_code": "J96.0", "name_ko": "급성 호흡부전", "name_en": "Acute respiratory failure", "category": "호흡부전"},
            {"diag_code": "J96.1", "name_ko": "만성 호흡부전", "name_en": "Chronic respiratory failure", "category": "호흡부전"},
            {"diag_code": "J96.9", "name_ko": "상세불명의 호흡부전", "name_en": "Respiratory failure, unspecified", "category": "호흡부전"},
        ]

        self.stdout.write("=" * 60)
        self.stdout.write("진단 마스터 데이터 추가 시작")
        self.stdout.write("=" * 60)

        created_count = 0
        updated_count = 0
        error_count = 0

        for data in diagnosis_data:
            try:
                diagnosis, created = DiagnosisMaster.objects.update_or_create(
                    diag_code=data['diag_code'],
                    defaults={
                        'name_ko': data['name_ko'],
                        'name_en': data.get('name_en', ''),
                        'category': data.get('category', ''),
                        'is_active': True
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"[+] 추가: [{data['diag_code']}] {data['name_ko']}"))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"[*] 업데이트: [{data['diag_code']}] {data['name_ko']}"))

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"[!] 오류: [{data['diag_code']}] {data['name_ko']} - {str(e)}"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("작업 완료")
        self.stdout.write("=" * 60)
        self.stdout.write(f"[+] 추가됨: {created_count}개")
        self.stdout.write(f"[*] 업데이트됨: {updated_count}개")
        self.stdout.write(f"[!] 오류: {error_count}개")
        self.stdout.write(f"[=] 전체: {created_count + updated_count}개")
        self.stdout.write("=" * 60)

        # 카테고리별 통계
        self.stdout.write("\n[=] 카테고리별 통계:")
        categories = DiagnosisMaster.objects.values('category').distinct()
        for cat in categories:
            count = DiagnosisMaster.objects.filter(category=cat['category']).count()
            self.stdout.write(f"  - {cat['category']}: {count}개")
