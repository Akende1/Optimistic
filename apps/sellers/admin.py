from django.contrib import admin
from .models import Seller, SellerVerification


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    """
    Seller admin with verification control.
    """
    list_display = ['store_name', 'user', 'phone', 'verified', 'created_at']
    list_filter = ['verified', 'created_at']
    search_fields = ['store_name', 'user__username', 'phone']
    readonly_fields = ['created_at']
    
    actions = ['verify_sellers', 'unverify_sellers']
    
    def verify_sellers(self, request, queryset):
        """Verify selected sellers."""
        count = queryset.update(verified=True)
        self.message_user(request, f'{count} seller(s) verified successfully.')
    verify_sellers.short_description = 'Verify selected sellers'
    
    def unverify_sellers(self, request, queryset):
        """Unverify selected sellers."""
        count = queryset.update(verified=False)
        self.message_user(request, f'{count} seller(s) unverified.')
    unverify_sellers.short_description = 'Unverify selected sellers'
    
    fieldsets = (
        ('Seller Information', {
            'fields': ('user', 'store_name', 'phone')
        }),
        ('Verification', {
            'fields': ('verified',),
            'description': 'Sellers must be verified to publish products.'
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(SellerVerification)
class SellerVerificationAdmin(admin.ModelAdmin):
    """Admin view for KYC document review."""
    list_display = ['seller', 'status', 'submitted_at', 'reviewed_at', 'reviewed_by']
    list_filter = ['status', 'submitted_at', 'reviewed_at']
    search_fields = ['seller__store_name', 'seller__user__username', 'government_id_number']
    readonly_fields = ['submitted_at', 'reviewed_at', 'reviewed_by', 'rejection_reason']

    fieldsets = (
        ('Seller', {
            'fields': ('seller',)
        }),
        ('Identity Documents', {
            'fields': ('government_id_type', 'government_id_number', 'government_id_front', 'government_id_back', 'selfie_with_id')
        }),
        ('Review', {
            'fields': ('status', 'rejection_reason', 'submitted_at', 'reviewed_at', 'reviewed_by')
        }),
    )
