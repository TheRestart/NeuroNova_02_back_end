from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.conf import settings
import uuid


class UserManager(BaseUserManager):
    """Custom User Manager"""
    
    def create_user(self, username, email, password=None, **extra_fields):
        """일반 사용자 생성"""
        if not username:
            raise ValueError('Username is required')
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """슈퍼유저 생성"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('full_name', 'Administrator')
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """CDSS Custom User - 7개 역할"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('doctor', 'Doctor'),
        ('rib', 'Radiologist'),
        ('lab', 'Laboratory Technician'),
        ('nurse', 'Nurse'),
        ('patient', 'Patient'),
        ('external', 'External Organization'),
    ]
    
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    # Profile fields
    full_name = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    
    # Status fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'role', 'full_name']
    
    class Meta:
        db_table = 'acct_users'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def get_full_name(self):
        return self.full_name
    
    def get_short_name(self):
        return self.username


class Alert(models.Model):
    """
    사용자 알림 모델 (UC07)
    - 시스템 이벤트(AI 완료, 이상 징후 등)를 사용자에게 알림
    - WebSocket으로 실시간 전송 후 영속화
    """
    ALERT_TYPES = (
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
        ('SUCCESS', 'Success'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alerts')
    message = models.TextField(help_text="알림 내용")
    type = models.CharField(max_length=20, choices=ALERT_TYPES, default='INFO')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(null=True, blank=True, help_text="추가 데이터 (Link 등)")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type}] {self.user.username} - {self.message[:20]}"
