from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'full_name', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'full_name')
    ordering = ('-created_at',)
    readonly_fields = ('user_id', 'created_at', 'last_login')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user_id', 'username', 'email', 'password')
        }),
        ('Profile', {
            'fields': ('role', 'full_name', 'department', 'license_number')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_login')
        }),
    )
    
    add_fieldsets = (
        ('Create User', {
            'fields': ('username', 'email', 'password', 'role', 'full_name')
        }),
    )
