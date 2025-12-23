import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        # 인증된 사용자만 허용
        if not self.user.is_authenticated:
            await self.close()
            return

        # 사용자별 그룹 이름 생성 (예: user_1234)
        self.group_name = f"user_{self.user.username}"

        # 그룹에 추가
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # 그룹에서 제거
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # 클라이언트로부터 메시지 수신 (필요 시 처리)
        pass

    # 그룹 메시지 핸들러
    async def send_notification(self, event):
        message = event['message']
        alert_type = event.get('type', 'INFO')
        metadata = event.get('metadata', {})

        # WebSocket으로 전송
        await self.send(text_data=json.dumps({
            'message': message,
            'type': alert_type,
            'metadata': metadata
        }))
