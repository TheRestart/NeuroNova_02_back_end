from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import UserSerializer, UserCreateSerializer, LoginSerializer
from .permissions import IsAdmin
from .services import AuthService, UserService


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """로그인 - JWT 토큰 발급"""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    password = serializer.validated_data['password']

    # Service 레이어 사용
    result = AuthService.login(username, password)
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """로그아웃 - Refresh 토큰 블랙리스트"""
    refresh_token = request.data.get('refresh')

    # Service 레이어 사용
    result = AuthService.logout(request.user, refresh_token)
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """현재 사용자 정보"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """User CRUD (Admin only)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """회원가입"""
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # JWT 토큰 생성
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)
