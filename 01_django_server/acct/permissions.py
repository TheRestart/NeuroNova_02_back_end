from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Admin만 접근 가능"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsDoctor(permissions.BasePermission):
    """Doctor만 접근 가능"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'doctor'


class IsRIB(permissions.BasePermission):
    """Radiologist만 접근 가능"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'rib'


class IsLab(permissions.BasePermission):
    """Lab Technician만 접근 가능"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'lab'


class IsNurse(permissions.BasePermission):
    """Nurse만 접근 가능"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'nurse'


class IsDoctorOrRIB(permissions.BasePermission):
    """Doctor 또는 Radiologist만 접근"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['doctor', 'rib']


class IsDoctorOrNurse(permissions.BasePermission):
    """Doctor 또는 Nurse만 접근"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['doctor', 'nurse']


class IsSelfOrAdmin(permissions.BasePermission):
    """본인 또는 Admin만 접근 (Patient용)"""
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.role == 'admin':
            return True
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj.user_id == request.user.user_id


class IsStaffRole(permissions.BasePermission):
    """Staff 역할 (Doctor, RIB, Lab, Nurse, Admin)"""
    def has_permission(self, request, view):
        STAFF_ROLES = ['admin', 'doctor', 'rib', 'lab', 'nurse']
        return request.user.is_authenticated and request.user.role in STAFF_ROLES


class IsAdminOrReadOnly(permissions.BasePermission):
    """Admin만 쓰기, 나머지는 읽기만"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role == 'admin'
