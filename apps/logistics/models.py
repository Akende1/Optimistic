from django.db import models
from django.conf import settings
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone


class DeliveryPartner(models.Model):
    """
    Delivery partners - Zambian logistics reality.
    
    Purpose: Model how deliveries actually work in Zambia
    
    Partner Types (Zambian Context):
    - RIDER: Motorcycle/bicycle (fast, urban, same-day)
    - COURIER: Professional service (tracking, insurance, expensive)
    - BUS: Bus station delivery (common in Zambia! cheap, long-distance)
    - SELF: Seller delivers personally (trust, flexibility, cheap)
    
    Why This Matters:
    - Not all towns have courier services
    - Bus delivery is culturally accepted and common
    - Self-delivery builds trust (meet the seller)
    - Platform supports reality, not just ideal
    
    Service Area: Where they operate (e.g., "Lusaka CBD, Kabulonga")
    - Helps admin assign right partner for destination
    - Prevents sending urban rider to rural area
    
    is_active: Temporarily disable without deleting
    - Partner on vacation
    - Temporarily suspended
    - Can reactivate later
    
    Future: GPS tracking, ratings, auto-assignment, route optimization
    """
    PARTNER_TYPE_CHOICES = (
        ('RIDER', 'Motorcycle Rider'),
        ('COURIER', 'Courier Service'),
        ('BUS', 'Bus Station'),
        ('SELF', 'Seller Self-Delivery'),
    )

    # Link to User account (for login and authentication)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='delivery_partner_profile',
        help_text='User account for partner login (if applicable)'
    )
    
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    partner_type = models.CharField(max_length=10, choices=PARTNER_TYPE_CHOICES, default='RIDER')
    service_area = models.CharField(max_length=200, help_text='e.g., Lusaka CBD, Kabulonga, Chilenje')
    
    # Verification & Status
    verified = models.BooleanField(
        default=False,
        help_text='Admin verified this partner (ID, background check, etc.)'
    )
    is_active = models.BooleanField(default=True)
    
    # Additional Details
    vehicle_type = models.CharField(
        max_length=50,
        blank=True,
        help_text='e.g., Motorcycle, Van, Bicycle'
    )
    id_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='National ID or Driver License number'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Delivery Partner'
        verbose_name_plural = 'Delivery Partners'

    def __str__(self):
        return f"{self.name} ({self.get_partner_type_display()})"


class Delivery(models.Model):
    """
    Delivery tracking for orders - Zambian logistics reality.
    
    Design Philosophy:
    - Start simple: Status updates, no GPS required
    - Grow smart: Add GPS tracking when budget allows
    - Reality-first: Support multiple delivery methods (riders, bus, courier)
    
    Why This Approach?
    - GPS tracking is expensive (hardware, data costs)
    - Most Zambian deliveries use basic coordination (phone calls)
    - Status updates give enough visibility for MVP
    - Can add GPS later without breaking existing code
    
    Delivery Flow:
    1. Order placed → Delivery created (status=REQUESTED)
    2. Admin assigns partner → status=ASSIGNED
    3. Partner picks up → status=PICKED_UP
    4. Partner in transit → status=IN_TRANSIT
    5. Delivered to buyer → status=DELIVERED
    
    Alternative flows:
    - Delivery failed (address wrong, buyer unavailable) → FAILED
    - Order cancelled before delivery → CANCELLED
    
    Each status change updates timestamp fields (assigned_at, delivered_at, etc.)
    """
    
    # Status progression: Tracks delivery lifecycle
    STATUS_CHOICES = (
        ('REQUESTED', 'Requested'),   # Delivery created, awaiting assignment
        ('ASSIGNED', 'Assigned'),     # Partner assigned, not picked up yet
        ('PICKED_UP', 'Picked Up'),   # Partner has the package
        ('IN_TRANSIT', 'In Transit'), # On the way to buyer
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),   # Successfully delivered
        ('FAILED', 'Failed'),         # Delivery attempt failed
        ('EXCEPTION', 'Delivery Exception'),
        ('RETURNED', 'Returned'),
        ('LOST', 'Lost'),
        ('CANCELLED', 'Cancelled'),   # Order cancelled, delivery void
    )

    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='delivery'
    )
    partner = models.ForeignKey(
        DeliveryPartner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries'
    )

    # Addresses
    pickup_address = models.TextField(help_text='Seller location')
    delivery_address = models.TextField(help_text='Buyer location')

    # Pricing
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Delivery'
        verbose_name_plural = 'Deliveries'
        ordering = ['-created_at']

    def __str__(self):
        return f"Delivery for Order #{self.order.id} - {self.get_status_display()}"


class DeliveryEvent(models.Model):
    """Append-only, deduplicated carrier/courier tracking event."""
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='events')
    external_event_id = models.CharField(max_length=150)
    source = models.CharField(max_length=40)
    status = models.CharField(max_length=20, choices=Delivery.STATUS_CHOICES)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    occurred_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['occurred_at', 'id']
        constraints = [models.UniqueConstraint(fields=['source', 'external_event_id'], name='unique_delivery_source_event')]


class ShippingRate(models.Model):
    """Versioned rate used to quote package delivery by chargeable weight."""
    service_code = models.CharField(max_length=40)
    shipping_class = models.CharField(max_length=30, default='STANDARD')
    base_fee = models.DecimalField(max_digits=10, decimal_places=2)
    per_kg_fee = models.DecimalField(max_digits=10, decimal_places=2)
    dimensional_divisor = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('5000.00'))
    effective_from = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-effective_from']


class Package(models.Model):
    """Immutable-at-handover physical parcel for one seller fulfillment."""
    fulfillment = models.ForeignKey('orders.OrderFulfillment', on_delete=models.PROTECT, related_name='packages')
    shipping_rate = models.ForeignKey(ShippingRate, on_delete=models.PROTECT, related_name='packages')
    weight_kg = models.DecimalField(max_digits=8, decimal_places=3)
    dimensional_weight_kg = models.DecimalField(max_digits=8, decimal_places=3)
    chargeable_weight_kg = models.DecimalField(max_digits=8, decimal_places=3)
    length_cm = models.DecimalField(max_digits=8, decimal_places=2)
    width_cm = models.DecimalField(max_digits=8, decimal_places=2)
    height_cm = models.DecimalField(max_digits=8, decimal_places=2)
    quoted_fee = models.DecimalField(max_digits=10, decimal_places=2)
    declared_value = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


class CustodyEvent(models.Model):
    """Append-only proof of a physical package transfer between parties."""
    EVENT_CHOICES = (('SELLER_RELEASED', 'Seller Released'), ('COURIER_RECEIVED', 'Courier Received'), ('BUS_OPERATOR_RECEIVED', 'Bus Operator Received'), ('DESTINATION_ARRIVED', 'Destination Arrived'), ('BUYER_RECEIVED', 'Buyer Received'))
    package = models.ForeignKey(Package, on_delete=models.PROTECT, related_name='custody_events')
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    external_reference = models.CharField(max_length=150, unique=True)
    releasing_party = models.CharField(max_length=150)
    receiving_party = models.CharField(max_length=150)
    location = models.CharField(max_length=200)
    waybill_number = models.CharField(max_length=100, blank=True)
    seal_identifier = models.CharField(max_length=100, blank=True)
    verification_method = models.CharField(max_length=30, default='OTP')
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='recorded_custody_events')
    occurred_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class ReturnRequest(models.Model):
    """Reverse-logistics aggregate; financial outcomes are delegated to finance services."""
    STATUS_CHOICES = (('REQUESTED', 'Requested'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('COURIER_ASSIGNED', 'Courier Assigned'), ('PICKED_UP', 'Picked Up'), ('IN_TRANSIT', 'In Transit'), ('SELLER_RECEIVED', 'Seller Received'), ('CONDITION_VERIFIED', 'Condition Verified'), ('REFUND_AUTHORIZED', 'Refund Authorized'), ('CLOSED', 'Closed'))
    order = models.ForeignKey('orders.Order', on_delete=models.PROTECT, related_name='returns')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='return_requests')
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default='REQUESTED', db_index=True)
    reason = models.TextField()
    return_by = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ReturnLine(models.Model):
    CONDITION_CHOICES = (('UNOPENED', 'Unopened'), ('RESALEABLE', 'Resaleable'), ('DAMAGED', 'Damaged'), ('MISSING', 'Missing'))
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.PROTECT, related_name='lines')
    order_item = models.ForeignKey('orders.OrderItem', on_delete=models.PROTECT, related_name='return_lines')
    quantity = models.PositiveIntegerField()
    condition = models.CharField(max_length=15, choices=CONDITION_CHOICES, blank=True)
    inspection_notes = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['return_request', 'order_item'], name='unique_return_request_line')]


class ZambianLocation(models.Model):
    """
    Zambian provinces, cities, and delivery zones.
    
    Purpose: Standardize locations for delivery routing and partner assignment
    
    Why This Matters:
    - Consistent addressing across platform
    - Easy delivery partner assignment by zone
    - Shipping cost calculation by zone
    - Better analytics (orders by region)
    
    Hierarchy:
    - PROVINCE: Lusaka, Copperbelt, Southern, etc. (10 provinces)
    - CITY: Lusaka, Ndola, Kitwe, Livingstone, etc.
    - ZONE: Lusaka CBD, Kabulonga, Chilenje, etc. (neighborhoods/townships)
    
    Usage:
    - Buyers select from dropdowns during checkout
    - Delivery partners register their service zones
    - Admin assigns partners based on matching zones
    """
    LOCATION_TYPE_CHOICES = (
        ('PROVINCE', 'Province'),
        ('CITY', 'City'),
        ('ZONE', 'Zone/Area'),
    )
    
    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=10, choices=LOCATION_TYPE_CHOICES)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text='Parent location (Zone → City → Province)'
    )
    delivery_base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Base delivery cost for this location'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Zambian Location'
        verbose_name_plural = 'Zambian Locations'
        ordering = ['location_type', 'name']
        unique_together = ['name', 'location_type', 'parent']
    
    def __str__(self):
        if self.parent:
            return f"{self.name}, {self.parent.name}"
        return self.name
    
    def get_full_address(self):
        """Return full hierarchical address (Zone, City, Province)"""
        parts = [self.name]
        current = self.parent
        while current:
            parts.append(current.name)
            current = current.parent
        return ', '.join(parts)


class CourierWallet(models.Model):
    """
    Courier wallet - where delivery earnings accumulate.
    
    Purpose: Track courier earnings separately from seller escrow
    
    Separation of Concerns:
    - Couriers earn from deliveries, not orders
    - Cannot see order amounts
    - Cannot trigger payouts
    - Platform controls all transitions
    
    Money Flow:
    1. Delivery completed → pending_balance increases
    2. Buyer confirms → pending → available  
    3. Admin batches payout → available decreases
    
    Why Separate from Seller Escrow:
    - Different business model (per-delivery vs per-sale)
    - Different payout schedules
    - Different tax/compliance requirements
    """
    courier = models.OneToOneField(
        'DeliveryPartner',
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    available_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Confirmed earnings ready for payout'
    )
    pending_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Earnings awaiting delivery confirmation'
    )
    lifetime_earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Total earnings since registration'
    )
    last_payout_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last successful payout timestamp'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Courier Wallet'
        verbose_name_plural = 'Courier Wallets'
    
    def __str__(self):
        return f"{self.courier.name} - Available: K{self.available_balance}"
    
    def add_pending(self, amount):
        """Add to pending balance (delivery completed)."""
        if amount <= 0:
            raise ValidationError('Amount must be positive')
        self.pending_balance += amount
        self.save()
    
    def clear_pending(self, amount):
        """Move from pending to available (buyer confirmed)."""
        if amount <= 0:
            raise ValidationError('Amount must be positive')
        if amount > self.pending_balance:
            raise ValidationError('Insufficient pending balance')
        
        self.pending_balance -= amount
        self.available_balance += amount
        self.lifetime_earnings += amount
        self.save()
    
    def deduct_available(self, amount):
        """Deduct from available (payout processed)."""
        if amount <= 0:
            raise ValidationError('Amount must be positive')
        if amount > self.available_balance:
            raise ValidationError('Insufficient available balance')
        
        self.available_balance -= amount
        self.last_payout_at = timezone.now()
        self.save()


class CourierEarning(models.Model):
    """
    Individual courier earning record per delivery.
    
    Purpose: Granular tracking of courier compensation
    
    Why Track Each Delivery:
    - Dispute resolution needs specifics
    - Performance analytics per delivery
    - Variable rates (distance, time, urgency)
    - Audit trail for tax reporting
    
    Status Flow:
    - PENDING: Delivery marked complete by courier
    - CLEARED: Buyer confirmed delivery
    - PAID: Included in payout batch
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending Confirmation'),
        ('CLEARED', 'Cleared for Payout'),
        ('PAID', 'Paid Out'),
        ('DISPUTED', 'Under Dispute'),
        ('CANCELLED', 'Cancelled'),
    )
    
    delivery = models.OneToOneField(
        'Delivery',
        on_delete=models.PROTECT,
        related_name='earning'
    )
    courier = models.ForeignKey(
        'DeliveryPartner',
        on_delete=models.CASCADE,
        related_name='earnings'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Earning amount for this delivery'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    payout_batch = models.ForeignKey(
        'CourierPayoutBatch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='earnings'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    cleared_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Courier Earning'
        verbose_name_plural = 'Courier Earnings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['courier', 'status']),
        ]
    
    def __str__(self):
        return f"{self.courier.name} - K{self.amount} ({self.status})"
    
    def mark_cleared(self):
        """Mark as cleared (buyer confirmed delivery)."""
        if self.status != 'PENDING':
            raise ValidationError(f'Can only clear PENDING earnings. Current: {self.status}')
        
        self.status = 'CLEARED'
        self.cleared_at = timezone.now()
        self.save()
        
        # Move money in wallet
        wallet, _ = CourierWallet.objects.get_or_create(courier=self.courier)
        wallet.clear_pending(self.amount)
    
    def mark_paid(self, payout_batch):
        """Mark as paid (included in payout batch)."""
        if self.status != 'CLEARED':
            raise ValidationError(f'Can only pay CLEARED earnings. Current: {self.status}')
        
        self.status = 'PAID'
        self.paid_at = timezone.now()
        self.payout_batch = payout_batch
        self.save()
        
        # Deduct from wallet
        wallet = self.courier.wallet
        wallet.deduct_available(self.amount)
    
    @classmethod
    def create_for_delivery(cls, delivery, amount=None):
        """
        Create earning record when delivery completed.
        
        Args:
            delivery: Delivery instance
            amount: Earning amount (calculated from zone if None)
        """
        if hasattr(delivery, 'earning'):
            raise ValidationError('Delivery already has earning record')
        
        if amount is None:
            # Calculate from delivery zone
            amount = Decimal('50.00')  # TODO: Calculate from ZambianLocation
        
        earning = cls.objects.create(
            delivery=delivery,
            courier=delivery.courier,
            amount=amount,
            status='PENDING'
        )
        
        # Add to courier wallet pending
        wallet, _ = CourierWallet.objects.get_or_create(courier=delivery.courier)
        wallet.add_pending(amount)
        
        return earning


class CourierPayoutBatch(models.Model):
    """
    Courier payout batch - grouping earnings for payment.
    
    Purpose: Process multiple courier payouts efficiently
    
    Why Batch:
    - Reduce transaction fees
    - Weekly/monthly payment schedules
    - Easier accounting reconciliation
    - Admin review before release
    
    Separation of Concerns:
    - Only admins create batches
    - Couriers see batch in their earning history
    - Earnings link to batch (audit trail)
    - Platform tracks payout liability
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('PAID', 'Paid Out'),
        ('CANCELLED', 'Cancelled'),
    )
    
    period_start = models.DateField(
        help_text='Start date of earning period'
    )
    period_end = models.DateField(
        help_text='End date of earning period'
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Total payout amount for this batch'
    )
    courier_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of couriers in this batch'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    # Admin tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_payout_batches'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_payout_batches'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Courier Payout Batch'
        verbose_name_plural = 'Courier Payout Batches'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payout Batch {self.period_start} - {self.period_end} (K{self.total_amount})"
    
    def approve(self, approver):
        """Admin approves batch for payment."""
        if self.status != 'PENDING':
            raise ValidationError(f'Can only approve PENDING batches. Current: {self.status}')
        
        self.status = 'APPROVED'
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.save()
    
    def mark_paid(self):
        """Mark batch as paid (external payment completed)."""
        if self.status != 'APPROVED':
            raise ValidationError(f'Can only pay APPROVED batches. Current: {self.status}')
        
        # Mark all earnings as paid
        for earning in self.earnings.filter(status='CLEARED'):
            earning.mark_paid(self)
        
        self.status = 'PAID'
        self.paid_at = timezone.now()
        self.save()
