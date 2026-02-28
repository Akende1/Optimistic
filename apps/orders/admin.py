from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Order admin (stub for now).
    """
    list_display = ['id', 'buyer', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['buyer__username']
    readonly_fields = ['created_at']
    
    actions = ['mark_paid', 'mark_cancelled']
    
    def mark_paid(self, request, queryset):
        """Mark orders as paid."""
        count = queryset.update(status='PAID')
        self.message_user(request, f'{count} order(s) marked as paid.')
    mark_paid.short_description = 'Mark as paid'
    
    def mark_cancelled(self, request, queryset):
        """Mark orders as cancelled."""
        count = queryset.update(status='CANCELLED')
        self.message_user(request, f'{count} order(s) cancelled.')
    mark_cancelled.short_description = 'Mark as cancelled'
