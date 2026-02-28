from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Notification admin (view-only, system creates these).
    """
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['user', 'notification_type', 'title', 'message', 'related_id', 'created_at']

    def has_add_permission(self, request):
        """Notifications created by system only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Notifications are immutable."""
        return False
