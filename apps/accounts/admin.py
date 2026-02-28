from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from typing import Sequence


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin with role management.
    """
    list_display = ['username', 'email', 'role', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email']
    
    fieldsets = list(BaseUserAdmin.fieldsets) + [
        ('Role', {'fields': ('role',)}),
    ]
    
    add_fieldsets = list(BaseUserAdmin.add_fieldsets) + [
        ('Role', {'fields': ('role',)}),
    ]
