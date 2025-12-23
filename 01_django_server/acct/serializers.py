from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """User Serializer"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'user_id', 'username', 'email', 'role', 'role_display',
            'full_name', 'department', 'license_number',
            'is_active', 'created_at', 'last_login'
        ]
        read_only_fields = ['user_id', 'created_at', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        """비밀번호 해싱하여 User 생성"""
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class UserCreateSerializer(serializers.ModelSerializer):
    """회원가입용 Serializer"""
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'role', 'full_name', 'department', 'license_number'
        ]
    
    def validate(self, data):
        """비밀번호 확인"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        """비밀번호 확인 필드 제거 후 User 생성"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """로그인용 Serializer"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
