# RabbitMQ Message Queue

RabbitMQ는 AI 작업을 비동기로 처리하기 위한 메시지 큐 시스템입니다.

## 서버 정보

- **컨테이너 이름**: cdss-rabbitmq
- **AMQP 포트**: 5672
- **Management UI**: http://localhost:15672
- **Username**: guest
- **Password**: guest

## 실행 방법

```bash
# 컨테이너 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 컨테이너 중지
docker-compose down
```

## Management UI 접속

1. 브라우저에서 http://localhost:15672 접속
2. Username: `guest`, Password: `guest` 입력
3. "Queues" 탭에서 `ai_jobs` 큐 확인 가능

## Django 연동

Django의 `ai/queue_client.py`에서 RabbitMQ를 사용합니다:

```python
from ai.queue_client import AIQueueClient

client = AIQueueClient()
client.publish_ai_job({
    'study_id': 'abc-123',
    'dicom_data': 'base64_encoded_data'
})
```

## 큐 구조

- **큐 이름**: `ai_jobs`
- **메시지 형식**: JSON
- **영구 저장**: enabled (서버 재시작 시에도 메시지 유지)
