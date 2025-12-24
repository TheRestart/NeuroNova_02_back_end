from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Alert, User

class AuthService:
    @staticmethod
    def login(username, password):
        user = authenticate(username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }
        else:
            return {'error': 'Invalid credentials'}

    @staticmethod
    def logout(user, refresh_token):
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return {'success': 'Successfully logged out.'}
        except Exception as e:
            return {'error': str(e)}

class UserService:
    pass

class AlertService:
    @staticmethod
    def send_alert(user_id, message, alert_type='INFO', metadata=None):
        """
        특정 사용자에게 알림 생성 및 WebSocket 전송
        """
        if metadata is None:
            metadata = {}

        try:
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError):
            return None

        # 1. DB 저장 (영속화)
        alert = Alert.objects.create(
            user=user,
            message=message,
            type=alert_type,
            metadata=metadata
        )

        # 2. WebSocket 전송 (개별 전송)
        AlertService._broadcast_to_websocket(f"user_{user.username}", message, alert_type, metadata)

        return alert

    @staticmethod
    def send_role_alert(role, message, alert_type='INFO', metadata=None):
        """
        특정 역할을 가진 모든 사용자에게 알림 및 WebSocket 전송
        (DB 저장은 각 사용자별로 수행하거나, 시스템 알림용 별도 처리가 필요할 수 있음)
        """
        if metadata is None:
            metadata = {}

        users = User.objects.filter(role=role, is_active=True)
        
        # 각 사용자별로 DB 저장
        alerts = []
        for user in users:
            alerts.append(Alert(
                user=user,
                message=message,
                type=alert_type,
                metadata=metadata
            ))
        Alert.objects.bulk_create(alerts)

        # WebSocket 전송 (역할 그룹에 한 번만 전송)
        AlertService._broadcast_to_websocket(f"role_{role}", message, alert_type, metadata)
        
        return len(alerts)

    @staticmethod
    def _broadcast_to_websocket(group_name, message, alert_type, metadata):
        """Websocket 브로드캐스팅 로직 공통화"""
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'message': message,
                    'alert_type': alert_type,
                    'metadata': metadata
                }
            )
        except Exception as e:
            print(f"WebSocket broadcast failed for group {group_name}: {str(e)}")
