from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserSerializer

class AuthService:
    @staticmethod
    def login(username, password):
        user = authenticate(username=username, password=password)
        
        if user is None:
            return {'error': 'Invalid credentials'}
        
        if not user.is_active:
            return {'error': 'User is inactive'}
        
        # JWT 토큰 생성
        refresh = RefreshToken.for_user(user)
        
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }

    @staticmethod
    def logout(user, refresh_token):
        if not refresh_token:
            return {'error': 'Refresh token is required'}
            
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return {'message': 'Successfully logged out'}
        except Exception as e:
            return {'error': str(e)}

class UserService:
    @staticmethod
    def register_user(validated_data):
        """사용자 회원가입 처리"""
        from .models import User
        
        # 비밀번호 확인 필드 제거 (Serializer에서 이미 검증됨)
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

