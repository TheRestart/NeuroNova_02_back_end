from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Alert, User
from .serializers import UserSerializer

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
        알림 생성 및 WebSocket 전송
        """
        if metadata is None:
            metadata = {}

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

        # 1. DB 저장 (영속화)
        alert = Alert.objects.create(
            user=user,
            message=message,
            type=alert_type,
            metadata=metadata
        )

        # 2. WebSocket 전송 (Real-time)
        channel_layer = get_channel_layer()
        group_name = f"user_{user.username}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_notification',  # Consumer method name
                'message': message,
                'type': alert_type,
                'metadata': metadata
            }
        )

        return alert
