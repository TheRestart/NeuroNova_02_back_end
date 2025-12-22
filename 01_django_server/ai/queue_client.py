import pika
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class AIQueueClient:
    """RabbitMQ를 통한 AI Job Queue 클라이언트
    
    Flask AI Server가 추후 통합되면 이 큐에서 Job을 꺼내 처리합니다.
    """
    
    def __init__(self):
        try:
            credentials = pika.PlainCredentials(
                settings.RABBITMQ_USER,
                settings.RABBITMQ_PASSWORD
            )
            parameters = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # ai_jobs 큐 선언 (durable=True로 서버 재시작 시에도 유지)
            self.channel.queue_declare(queue='ai_jobs', durable=True)
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def publish_ai_job(self, job_data):
        """AI Job을 큐에 추가
        
        Args:
            job_data (dict): AI Job 정보
                {
                    'job_id': str,
                    'study_id': str,
                    'dicom_data': str (base64 encoded),
                    'model_type': str,
                    ...
                }
        
        Returns:
            bool: 성공 여부
        """
        try:
            message = json.dumps(job_data)
            self.channel.basic_publish(
                exchange='',
                routing_key='ai_jobs',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # persistent message
                    content_type='application/json'
                )
            )
            logger.info(f"Published AI job: {job_data.get('job_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish AI job: {e}")
            return False
    
    def close(self):
        """연결 종료"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
