# NeuroNova Backend Server

**현재 상태**: ✅ Week 4 완료 - Infrastructure 구축 완료
**Django 버전**: 5.0
**Python 버전**: 3.11+

---

## 📋 개요

NeuroNova 프로젝트의 Django REST API 백엔드 서버입니다.

### 구현 완료된 기능 (Week 4)
- ✅ **UC01 (ACCT)**: 인증/권한 7개 역할 (RBAC)
- ✅ **UC02 (EMR)**: OpenEMR 프록시, Write-Through 패턴
- ✅ **UC05 (RIS)**: Orthanc PACS 연동
- ✅ **UC06 (AI)**: RabbitMQ 큐 기본 구현
- ✅ MySQL 데이터베이스, 7-Layer Architecture

### 미구현 (타 팀원 담당)
- ⏸️ **UC03 (OCS)**: 처방전달시스템
- ⏸️ **UC04 (LIS)**: 임상병리정보시스템
- ⏸️ **UC07 (ALERT)**: 실시간 알림 (WebSocket/Channels)
- ⏸️ **UC08 (FHIR)**: FHIR 리소스 변환
- ⏸️ **UC09 (AUDIT)**: 감사 로그 확장

---

## ⚡ 현재 개발 상태 (2025-12-24)

### AI 코어 개발 단계 (Week 5-12)
현재는 **AI 코어 모델 개발**에 집중하고 있으며, Flask AI Serving 통합은 **Week 13**에 진행합니다.

**AI 개발자는 이 디렉토리를 수정할 필요 없음**
- AI 코어: `../05_ai_core/` 디렉토리에서 독립 개발
- Backend Serving: Week 13 통합 시 Flask API로 연결

---

## 🚀 빠른 시작 (Django 서버 실행)

```bash
# Django 서버 디렉토리로 이동
cd 01_django_server

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# Django 서버 실행
python manage.py runserver 0.0.0.0:8000
```

**서버 확인**: http://localhost:8000/api/

---

## 📖 주요 문서

### 프로젝트 전체 문서
- **[01_프로젝트_개요.md](../01_doc/01_프로젝트_개요.md)**: 프로젝트 전체 개요
- **[17_프로젝트_RR_역할분담.md](../01_doc/17_프로젝트_RR_역할분담.md)**: R&R 정의 및 개발 전략
- **[REF_CLAUDE_CONTEXT.md](../01_doc/REF_CLAUDE_CONTEXT.md)**: Claude AI 온보딩
- **[LOG_작업이력.md](../01_doc/LOG_작업이력.md)**: 작업 이력 및 현황

### Backend 관련 문서
- **[08_API_명세서.md](../01_doc/08_API_명세서.md)**: Django REST API 명세서
- **[09_데이터베이스_스키마.md](../01_doc/09_데이터베이스_스키마.md)**: DB 스키마 및 ERD
- **[06_환경설정_가이드.md](../01_doc/06_환경설정_가이드.md)**: 환경 설정 가이드

---

**Last Updated**: 2025-12-24
**Version**: 1.0 (Infrastructure Complete)
