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
        self.user_group = f"user_{self.user.username}"
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        # 역할별 그룹 이름 생성 (예: role_doctor)
        if hasattr(self.user, 'role') and self.user.role:
            self.role_group = f"role_{self.user.role}"
            await self.channel_layer.group_add(self.role_group, self.channel_name)
        else:
            self.role_group = None

        await self.accept()

    async def disconnect(self, close_code):
        # 그룹에서 제거
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        
        if getattr(self, 'role_group', None):
            await self.channel_layer.group_discard(self.role_group, self.channel_name)

    async def receive(self, text_data):
        # 클라이언트로부터 메시지 수신 (필요 시 처리)
        pass

    # 그룹 메시지 핸들러
    async def send_notification(self, event):
        message = event['message']
        alert_type = event.get('alert_type', 'INFO')
        metadata = event.get('metadata', {})

        # WebSocket으로 전송
        await self.send(text_data=json.dumps({
            'message': message,
            'type': alert_type,
            'metadata': metadata
        }))
