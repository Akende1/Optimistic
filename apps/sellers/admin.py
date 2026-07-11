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
    readonly_fields = ['created_at', 'verified', 'verification_status', 'verified_at', 'verified_by']
    
    actions = ['approve_completed_kyc', 'unverify_sellers']
    
    def approve_completed_kyc(self, request, queryset):
        approved, errors = 0, []
        for seller in queryset:
            try:
                seller.kyc_documents.approve(request.user)
                approved += 1
            except Exception as exc:
                errors.append(f'{seller.store_name}: {exc}')
        self.message_user(request, f'{approved} seller(s) approved. ' + (' | '.join(errors) if errors else ''))
    approve_completed_kyc.short_description = 'Approve sellers with complete KYC'
    
    def unverify_sellers(self, request, queryset):
        """Revoke commercial access and suspend public listings."""
        count = 0
        for seller in queryset:
            seller.verified = False
            seller.verification_status = 'REJECTED'
            seller.verification_notes = 'Verification revoked by administrator.'
            seller.save(update_fields=['verified', 'verification_status', 'verification_notes'])
            seller.products.filter(status='ACTIVE').update(status='SUSPENDED')
            count += 1
        self.message_user(request, f'{count} seller(s) unverified.')
    unverify_sellers.short_description = 'Unverify selected sellers'
    
    fieldsets = (
        ('Seller Information', {
            'fields': ('user', 'store_name', 'phone', 'business_type', 'business_name',
                       'business_registration_number', 'tax_pin', 'physical_address', 'primary_location')
        }),
        ('Payout ownership', {
            'fields': ('payout_method', 'payout_provider', 'payout_account_name',
                       'payout_account_number', 'payout_account_verified')
        }),
        ('Verification', {
            'fields': ('verified', 'verification_status', 'verified_at', 'verified_by'),
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
