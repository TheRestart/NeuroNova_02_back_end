# Orthanc PACS Server

Orthanc는 경량 오픈소스 DICOM 서버입니다. CDSS 시스템에서 의료 영상을 저장하고 조회하는 데 사용됩니다.

## 서버 정보

- **컨테이너 이름**: cdss-orthanc
- **웹 UI**: http://localhost:8042
- **DICOM 포트**: 4242
- **Username**: orthanc
- **Password**: orthanc123

## 실행 방법

```bash
# 컨테이너 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 컨테이너 중지
docker-compose down

# 데이터 포함 완전 삭제
docker-compose down -v
```

## 웹 UI 접속

1. 브라우저에서 http://localhost:8042 접속
2. Username: `orthanc`, Password: `orthanc123` 입력
3. "Upload" 버튼으로 DICOM 파일 업로드 가능

## DICOMweb API

Django에서 다음 API를 통해 Orthanc와 통신합니다:

- `GET /studies` - 모든 Study 목록
- `GET /studies/{id}` - Study 상세 정보
- `POST /tools/find` - DICOM 검색
- `GET /instances/{id}/file` - DICOM 파일 다운로드

## 테스트 DICOM 샘플

온라인에서 무료 DICOM 샘플 다운로드:
- https://www.dicomlibrary.com/
- https://wiki.cancerimagingarchive.net/display/Public/Collections
