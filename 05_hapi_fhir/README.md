# HAPI FHIR JPA Server

Clinical Decision Support System (CDSS)의 의료 데이터 교환 및 저장을 위한 HL7 FHIR 서버입니다.

## 개요
- **버전**: FHIR R4
- **이미지**: `hapiproject/hapi:latest`
- **Port**: 8080

## 실행 방법

```bash
docker-compose up -d
```

## 접속 정보
- **Web UI**: http://localhost:8080/fhir/
- **Capability Statement**: http://localhost:8080/fhir/metadata

## 주요 리소스
- Patient
- Encounter
- ServiceRequest (Radiology Order)
- ImagingStudy (Radiology Study)
- DiagnosticReport (AI Result)
