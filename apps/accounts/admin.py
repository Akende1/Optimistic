from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AccountVerificationCode
from typing import Sequence


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin with role management.
    """
    list_display = ['username', 'email', 'role', 'phone_number', 'phone_verified', 'email_verified', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['role', 'phone_verified', 'email_verified', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'phone_number']
    
    fieldsets = list(BaseUserAdmin.fieldsets) + [
        ('Contact', {'fields': ('phone_number', 'phone_verified', 'phone_verified_at', 'email_verified', 'email_verified_at')}),
        ('Role', {'fields': ('role',)}),
    ]
    
    add_fieldsets = list(BaseUserAdmin.add_fieldsets) + [
        ('Role', {'fields': ('role',)}),
    ]


@admin.register(AccountVerificationCode)
class AccountVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'channel', 'purpose', 'code', 'expires_at', 'used_at', 'attempts', 'created_at']
    list_filter = ['channel', 'purpose', 'created_at', 'used_at']
    search_fields = ['user__username', 'user__email', 'user__phone_number', 'code']
    readonly_fields = ['user', 'channel', 'purpose', 'code', 'expires_at', 'used_at', 'attempts', 'max_attempts', 'created_at']
