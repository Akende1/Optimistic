from django.contrib import admin
from django.utils import timezone
from .models import Review, Report


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Review admin (read-only, reviews are permanent).
    """
    list_display = ['reviewer', 'product', 'seller', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['reviewer__username', 'product__name', 'comment']
    readonly_fields = ['order', 'product', 'seller', 'reviewer', 'rating', 'comment', 'created_at']

    def has_add_permission(self, request):
        """Reviews created by users only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Reviews are permanent."""
        return False


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    Report admin for moderation.
    """
    list_display = ['reporter', 'target_type', 'target_id', 'reason', 'status', 'created_at']
    list_filter = ['target_type', 'reason', 'status', 'created_at']
    search_fields = ['reporter__username', 'description']
    readonly_fields = ['reporter', 'target_type', 'target_id', 'reason', 'description', 'created_at']

    actions = ['mark_reviewing', 'mark_actioned', 'mark_dismissed']

    def mark_reviewing(self, request, queryset):
        """Mark reports as under review."""
        count = queryset.update(status='REVIEWING', reviewed_at=timezone.now())
        self.message_user(request, f'{count} report(s) under review.')
    mark_reviewing.short_description = 'Mark as reviewing'

    def mark_actioned(self, request, queryset):
        """Mark reports as actioned."""
        count = queryset.update(status='ACTIONED', reviewed_at=timezone.now())
        self.message_user(request, f'{count} report(s) actioned.')
    mark_actioned.short_description = 'Mark as actioned'

    def mark_dismissed(self, request, queryset):
        """Dismiss reports."""
        count = queryset.update(status='DISMISSED', reviewed_at=timezone.now())
        self.message_user(request, f'{count} report(s) dismissed.')
    mark_dismissed.short_description = 'Dismiss reports'

    fieldsets = (
        ('Report Information', {
            'fields': ('reporter', 'target_type', 'target_id', 'reason', 'description')
        }),
        ('Moderation', {
            'fields': ('status', 'admin_notes', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
