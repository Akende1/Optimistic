from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with role-based behavior.
    
    Design Philosophy:
    - Single identity, multiple capabilities (no separate Buyer/Seller user tables)
    - Role determines behavior, not user type
    - One user can potentially switch roles (future-proof)
    
    Why Custom User?
    - Django best practice: always use custom user from day one
    - Allows adding fields without complex migrations later
    - Centralizes authentication logic
    
    Inherits from AbstractUser:
    - Gets username, password, email, first_name, last_name
    - Gets is_staff, is_active, is_superuser
    - Gets date_joined, last_login
    - Full Django auth system compatibility
    """
    
    # Role choices: Define who can do what in the system
    ROLE_CHOICES = (
        ('BUYER', 'Buyer'),      # Can browse and purchase products
        ('SELLER', 'Seller'),    # Can list and manage products (if verified)
        ('COURIER', 'Courier'),  # Can handle deliveries (if verified)
        ('ADMIN', 'Admin'),      # Can manage the entire platform
    )
    
    # User lifecycle status
    STATUS_CHOICES = (
        ('REGISTERED', 'Registered'),
        ('VERIFIED', 'Verified'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('TERMINATED', 'Terminated'),
    )
    
    # Role field: Determines user capabilities throughout the system
    # Default to BUYER as most users will be customers
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='BUYER',
        db_index=True
    )
    
    # Status field: User lifecycle management
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='REGISTERED',
        help_text='User account status for lifecycle management'
    )
    
    # Superuser flag: Missing from Django 5.2+ auth migrations
    is_superuser = models.BooleanField(
        default=False,
        help_text='Designates that this user has all permissions without explicitly assigning them.'
    )
    
    # Suspension details
    suspended_at = models.DateTimeField(null=True, blank=True)
    suspension_reason = models.TextField(blank=True)
    
    # Profile picture: Optional for all users (especially buyers)
    profile_picture = models.ImageField(
        upload_to='users/profiles/',
        null=True,
        blank=True,
        help_text='Profile picture for user account'
    )
    
    # Phone verification for KYC
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text='Primary phone number for SMS verification'
    )
    phone_verified = models.BooleanField(
        default=False,
        help_text='Phone number verified via SMS code'
    )
    phone_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When phone was verified'
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __init__(self, *args, **kwargs):
        # Handle is_admin from Django migrations
        kwargs.pop('is_admin', None)
        super().__init__(*args, **kwargs)

    # Role check methods: Used for permission checking throughout the app
    # These make code more readable than checking role == 'SELLER' everywhere
    
    def is_seller(self):
        """Check if user has seller role (may not be verified yet)."""
        return self.role == 'SELLER'

    def is_buyer(self):
        """Check if user has buyer role."""
        return self.role == 'BUYER'
    
    def is_courier(self):
        """Check if user has courier role (may not be verified yet)."""
        return self.role == 'COURIER'

    def is_admin(self):
        """Check if user is admin OR superuser (superuser overrides everything)."""
        return self.role == 'ADMIN' or self.is_superuser
    
    def can_act(self):
        """Check if user can perform actions (not suspended or terminated)."""
        return self.status in ['VERIFIED', 'ACTIVE'] and self.is_active
    
    def suspend(self, reason=''):
        """Suspend user account."""
        from django.utils import timezone
        self.status = 'SUSPENDED'
        self.suspended_at = timezone.now()
        self.suspension_reason = reason
        self.is_active = False
        self.save()
    
    def reinstate(self):
        """Reinstate suspended user."""
        self.status = 'ACTIVE'
        self.suspended_at = None
        self.suspension_reason = ''
        self.is_active = True
        self.save()

    def __str__(self):
        """Human-readable representation shown in admin and logs."""
        return f"{self.username} ({self.get_role_display()}) - {self.get_status_display()}"


class BuyerAddress(models.Model):
    """
    Saved shipping addresses for buyers.
    
    Design:
    - Buyers can save multiple addresses (Home, Work, etc.)
    - One address can be marked as default
    - Delivery notes support GPS coordinates and landmarks for rural areas
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        help_text='Buyer who owns this address'
    )
    label = models.CharField(
        max_length=50,
        default='Home',
        help_text='Address nickname (Home, Work, etc.)'
    )
    street_address = models.TextField(
        help_text='Street/building/plot number'
    )
    town_city = models.CharField(
        max_length=100,
        help_text='Town or city name'
    )
    province = models.CharField(
        max_length=100,
        help_text='Province name'
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        help_text='Optional postal code'
    )
    delivery_notes = models.TextField(
        blank=True,
        help_text='GPS coordinates, landmarks, gate instructions'
    )
    is_default = models.BooleanField(
        default=False,
        help_text='Use this address by default at checkout'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Buyer Address'
        verbose_name_plural = 'Buyer Addresses'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.label} ({self.town_city})"
    
    def save(self, *args, **kwargs):
        """Ensure only one default address per user."""
        if self.is_default:
            # Set all other addresses for this user to non-default
            BuyerAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class PaymentMethod(models.Model):
    """
    Saved payment methods for buyers.
    
    Zambian Context:
    - Mobile money dominates (MTN MoMo, Airtel Money, Zamtel)
    - Card payments are secondary
    - Account identifiers are encrypted for security
    """
    METHOD_CHOICES = (
        ('MOBILE_MONEY', 'Mobile Money'),
        ('CARD', 'Debit/Credit Card'),
        ('WALLET', 'Optimistic Wallet'),
    )
    
    PROVIDER_CHOICES = (
        ('MTN_MOMO', 'MTN Mobile Money'),
        ('AIRTEL_MONEY', 'Airtel Money'),
        ('ZAMTEL', 'Zamtel Kwacha'),
        ('VISA', 'Visa'),
        ('MASTERCARD', 'Mastercard'),
        ('OPTIMISTIC', 'Optimistic Wallet'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payment_methods',
        help_text='Buyer who owns this payment method'
    )
    method_type = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        help_text='Type of payment method'
    )
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        help_text='Payment provider'
    )
    account_identifier = models.CharField(
        max_length=255,
        help_text='Encrypted phone number or card token'
    )
    account_name = models.CharField(
        max_length=100,
        help_text='Account holder name'
    )
    is_default = models.BooleanField(
        default=False,
        help_text='Use this payment method by default'
    )
    verified = models.BooleanField(
        default=False,
        help_text='Payment method verified (e.g., SMS code sent)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_provider_display()}"
    
    def save(self, *args, **kwargs):
        """Ensure only one default payment method per user."""
        if self.is_default:
            PaymentMethod.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
