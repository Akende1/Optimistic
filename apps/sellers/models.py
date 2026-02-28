from django.db import models
from django.conf import settings


class Seller(models.Model):
    """
    Seller profile extending User model.
    
    Business Rules:
    - Cannot publish products unless verified=True
    - Verification is manual (admin must approve)
    - OneToOne with User means each user can have only one seller profile
    
    Why Separate Model?
    - Not all users are sellers (keeps User table clean)
    - Seller-specific fields don't clutter User model
    - Easy to add seller verification workflow
    - Can add more seller-specific fields later (ratings, commission, etc.)
    
    Verification Flow:
    1. User registers and creates seller profile
    2. Status: verified=False (cannot publish products yet)
    3. Admin reviews seller in Django Admin
    4. Admin sets verified=True
    5. Seller can now publish products
    """
    
    # Link to User: OneToOne ensures one user = one seller profile
    # CASCADE: If user is deleted, seller profile is deleted too
    # related_name='seller': Access via user.seller in code
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Always use settings, never hardcode User model
        on_delete=models.CASCADE,
        related_name='seller'
    )
    
    # Store information
    store_name = models.CharField(max_length=100, help_text="Public-facing store name")
    phone = models.CharField(max_length=20, help_text="Contact number for delivery coordination")
    
    # Profile Image
    profile_image = models.ImageField(
        upload_to='sellers/profiles/',
        blank=True,
        null=True,
        help_text="Store/seller profile picture"
    )
    
    # Store Banner
    banner_image = models.ImageField(
        upload_to='sellers/banners/',
        blank=True,
        null=True,
        help_text="Store banner/cover image"
    )
    
    # Store Description
    description = models.TextField(
        blank=True,
        help_text="Store description and about information"
    )
    
    # ============================================
    # KYC & VERIFICATION FIELDS
    # ============================================
    
    # Business Information (Optional for MSMEs, Required for Companies)
    BUSINESS_TYPE_CHOICES = (
        ('SOLE_TRADER', 'Sole Trader'),
        ('PARTNERSHIP', 'Partnership'),
        ('COMPANY', 'Registered Company'),
    )
    business_type = models.CharField(
        max_length=20,
        choices=BUSINESS_TYPE_CHOICES,
        blank=True,
        help_text="Type of business entity"
    )
    business_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Legal business name (if different from store name)"
    )
    business_registration_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="PACRA or BDS registration number"
    )
    tax_pin = models.CharField(
        max_length=50,
        blank=True,
        help_text="Tax Identification Number (TPIN)"
    )
    
    # Physical Business Address (Required)
    physical_address = models.TextField(
        blank=True,
        help_text="Business street address, plot number"
    )
    town_city = models.CharField(
        max_length=100,
        blank=True,
        help_text="Town or city"
    )
    province = models.CharField(
        max_length=100,
        blank=True,
        help_text="Province"
    )
    
    # Payout Information (Required for seller earnings)
    PAYOUT_METHOD_CHOICES = (
        ('BANK', 'Bank Account'),
        ('MOBILE_MONEY', 'Mobile Money'),
    )
    PAYOUT_PROVIDER_CHOICES = (
        ('MTN_MOMO', 'MTN Mobile Money'),
        ('AIRTEL_MONEY', 'Airtel Money'),
        ('ZAMTEL', 'Zamtel Kwacha'),
        ('BANK', 'Bank Transfer'),
    )
    payout_method = models.CharField(
        max_length=20,
        choices=PAYOUT_METHOD_CHOICES,
        blank=True,
        help_text="How seller receives payments"
    )
    payout_provider = models.CharField(
        max_length=20,
        choices=PAYOUT_PROVIDER_CHOICES,
        blank=True,
        help_text="Payment provider"
    )
    payout_account_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Account holder name (must match ID)"
    )
    payout_account_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Account number or mobile money phone number"
    )
    
    # Verification Status (More granular than verified=True/False)
    VERIFICATION_STATUS_CHOICES = (
        ('PENDING', 'Pending - Not Submitted'),
        ('SUBMITTED', 'Documents Submitted'),
        ('UNDER_REVIEW', 'Under Admin Review'),
        ('VERIFIED', 'Verified and Active'),
        ('REJECTED', 'Rejected - Resubmission Required'),
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='PENDING',
        help_text="Current KYC verification status"
    )
    verification_notes = models.TextField(
        blank=True,
        help_text="Admin notes on verification (visible to seller if rejected)"
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When seller was verified"
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_sellers',
        help_text="Admin who verified this seller"
    )
    
    # Verification gate: The key to marketplace trust
    # False by default - requires admin approval to sell
    verified = models.BooleanField(
        default=False,
        help_text="Must be True to publish products. Set by admin only.",
        db_index=True
    )
    
    # Timestamp: When seller profile was created
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Seller'
        verbose_name_plural = 'Sellers'

    def __str__(self):
        return f"{self.store_name} ({'Verified' if self.verified else 'Unverified'})"
    
    def can_publish_products(self):
        """Check if seller can publish products (must be fully verified)."""
        return self.verified and self.verification_status == 'VERIFIED'
    
    def get_completion_percentage(self):
        """Calculate profile completion percentage for better UX."""
        fields = [
            self.store_name,
            self.description,
            self.profile_image,
            self.banner_image,
            self.physical_address,
            self.town_city,
            self.province,
            self.payout_method,
            self.payout_account_name,
            self.payout_account_number,
        ]
        completed = sum(1 for field in fields if field)
        return int((completed / len(fields)) * 100)


class SellerVerification(models.Model):
    """
    KYC documents for seller identity verification.
    
    Design Philosophy:
    - Separate model keeps sensitive documents isolated
    - OneToOne relationship: one verification per seller
    - Admin-only access to ID documents
    - Immutable history for compliance audit trail
    
    Verification Process:
    1. Seller uploads ID documents
    2. Status: PENDING
    3. Admin reviews for authenticity
    4. Admin approves/rejects
    5. If approved: Seller.verified = True, status = VERIFIED
    6. If rejected: Seller notified with reason, can resubmit
    """
    
    ID_TYPE_CHOICES = (
        ('NRC', 'National Registration Card'),
        ('PASSPORT', 'Passport'),
        ('DRIVERS_LICENSE', "Driver's License"),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    seller = models.OneToOneField(
        Seller,
        on_delete=models.CASCADE,
        related_name='kyc_documents',
        help_text='Seller being verified'
    )
    
    # Identity Document Information
    government_id_type = models.CharField(
        max_length=20,
        choices=ID_TYPE_CHOICES,
        help_text='Type of government ID'
    )
    government_id_number = models.CharField(
        max_length=50,
        help_text='ID number (encrypted in production)'
    )
    government_id_front = models.ImageField(
        upload_to='kyc/ids/',
        help_text='Front of ID card'
    )
    government_id_back = models.ImageField(
        upload_to='kyc/ids/',
        help_text='Back of ID card'
    )
    selfie_with_id = models.ImageField(
        upload_to='kyc/selfies/',
        null=True,
        blank=True,
        help_text='Selfie holding ID (optional, for advanced fraud prevention)'
    )
    
    # Review Information
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When documents were submitted'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When admin reviewed the documents'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_kyc',
        help_text='Admin who reviewed this verification'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text='Verification status'
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text='Reason for rejection (shown to seller)'
    )
    
    class Meta:
        verbose_name = 'Seller Verification Documents'
        verbose_name_plural = 'Seller Verification Documents'
    
    def __str__(self):
        return f"{self.seller.store_name} - {self.get_status_display()}"
    
    def approve(self, admin_user):
        """Approve seller verification and activate seller account."""
        from django.utils import timezone
        self.status = 'APPROVED'
        self.reviewed_at = timezone.now()
        self.reviewed_by = admin_user
        self.save()
        
        # Update seller model
        self.seller.verified = True
        self.seller.verification_status = 'VERIFIED'
        self.seller.verified_at = timezone.now()
        self.seller.verified_by = admin_user
        self.seller.save()
    
    def reject(self, admin_user, reason):
        """Reject seller verification with reason."""
        from django.utils import timezone
        self.status = 'REJECTED'
        self.reviewed_at = timezone.now()
        self.reviewed_by = admin_user
        self.rejection_reason = reason
        self.save()
        
        # Update seller model
        self.seller.verified = False
        self.seller.verification_status = 'REJECTED'
        self.seller.verification_notes = reason
        self.seller.save()
