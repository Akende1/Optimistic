from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid


class CommissionRule(models.Model):
    """
    Platform commission rules - the money truth.
    
    Purpose: Define how the platform earns from transactions
    
    Separation of Concerns:
    - Admins configure rules
    - System applies rules automatically
    - Sellers never see gross revenue
    - Rules are versioned (effective_from)
    
    Business Rules:
    - Default percentage applies to all categories
    - Category-specific rates override default
    - Rules effective from date (historical accuracy)
    - Multiple active rules allowed (category vs default)
    
    Why This Matters:
    - Can change commission without breaking historical orders
    - Can have category-specific pricing (e.g., electronics 5%, food 3%)
    - Transparent: sellers know rates before listing
    """
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Commission percentage (e.g., 10.00 for 10%)'
    )
    category = models.ForeignKey(
        'products.Category',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='commission_rules',
        help_text='Leave blank for default rule'
    )
    effective_from = models.DateTimeField(
        default=timezone.now,
        help_text='When this rule becomes active'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Active rules are applied to new orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Commission Rule'
        verbose_name_plural = 'Commission Rules'
        ordering = ['-effective_from']
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        category_name = self.category.name if self.category else 'Default'
        return f"{category_name}: {self.percentage}% (from {self.effective_from.date()})"
    
    def clean(self):
        """Validate commission percentage."""
        if self.percentage < 0 or self.percentage > 100:
            raise ValidationError('Commission percentage must be between 0 and 100')
    
    @classmethod
    def get_rate_for_product(cls, product, order_date=None):
        """
        Get applicable commission rate for a product.
        
        Args:
            product: Product instance
            order_date: Date to check rules (defaults to now)
        
        Returns:
            Decimal: Commission percentage
        """
        if order_date is None:
            order_date = timezone.now()
        
        # Try category-specific rule first
        if product.category:
            category_rule = cls.objects.filter(
                category=product.category,
                is_active=True,
                effective_from__lte=order_date
            ).first()
            if category_rule:
                return category_rule.percentage
        
        # Fall back to default rule
        default_rule = cls.objects.filter(
            category__isnull=True,
            is_active=True,
            effective_from__lte=order_date
        ).first()
        
        if default_rule:
            return default_rule.percentage
        
        # Emergency fallback (should never happen in production)
        return Decimal('10.00')


class EscrowAccount(models.Model):
    """
    Seller escrow account - where seller earnings wait.
    
    Purpose: Separate pending vs available money
    
    Money Flow:
    1. Order delivered → pending_balance increases
    2. Buyer confirms → pending → available
    3. Payout processed → available decreases
    
    Separation of Concerns:
    - Sellers see balances (read-only)
    - System controls transitions
    - Admin can view, not edit directly
    - Auditable: every change logged
    
    Why Two Balances:
    - pending: Money earned but not confirmed
    - available: Ready for payout
    - Prevents premature payouts before delivery confirmation
    """
    seller = models.OneToOneField(
        'sellers.Seller',
        on_delete=models.CASCADE,
        related_name='escrow_account'
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
        help_text='Total earnings since account creation'
    )
    last_payout_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last successful payout timestamp'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Escrow Account'
        verbose_name_plural = 'Escrow Accounts'
    
    def __str__(self):
        return f"{self.seller.store_name} - Available: K{self.available_balance}"
    
    def add_pending(self, amount):
        """Add to pending balance (order delivered, awaiting confirmation)."""
        if amount <= 0:
            raise ValidationError('Amount must be positive')
        self.pending_balance += amount
        self.save()
    
    def release_pending(self, amount):
        """
        Move from pending to available (buyer confirmed delivery).
        
        This is the trust gate: money moves from "maybe" to "yours".
        """
        if amount <= 0:
            raise ValidationError('Amount must be positive')
        if amount > self.pending_balance:
            raise ValidationError('Insufficient pending balance')
        
        self.pending_balance -= amount
        self.available_balance += amount
        self.lifetime_earnings += amount
        self.save()
    
    def deduct_available(self, amount):
        """Deduct from available balance (payout processed)."""
        if amount <= 0:
            raise ValidationError('Amount must be positive')
        if amount > self.available_balance:
            raise ValidationError('Insufficient available balance')
        
        self.available_balance -= amount
        self.last_payout_at = timezone.now()
        self.save()
    
    def refund_to_pending(self, amount):
        """Refund money back to pending (dispute resolution)."""
        if amount <= 0:
            raise ValidationError('Amount must be positive')
        if amount > self.available_balance:
            raise ValidationError('Insufficient available balance for refund')
        
        self.available_balance -= amount
        # Money goes back to platform, not pending
        # (pending is for unconfirmed deliveries only)
        self.save()


class LedgerTransaction(models.Model):
    """Immutable business event grouping balanced debit and credit entries."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=160, unique=True)
    event_type = models.CharField(max_length=50, db_index=True)
    order = models.ForeignKey('orders.Order', on_delete=models.PROTECT, null=True, blank=True, related_name='ledger_transactions')
    currency = models.CharField(max_length=3, default='ZMW')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk and LedgerTransaction.objects.filter(pk=self.pk).exists():
            raise ValidationError('Ledger transactions are immutable.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Ledger transactions cannot be deleted.')


class LedgerEntry(models.Model):
    """Immutable debit or credit posted to a named platform control account."""
    SIDE_CHOICES = (('DEBIT', 'Debit'), ('CREDIT', 'Credit'))
    transaction = models.ForeignKey(LedgerTransaction, on_delete=models.PROTECT, related_name='entries')
    account = models.CharField(max_length=80, db_index=True)
    side = models.CharField(max_length=6, choices=SIDE_CHOICES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    seller = models.ForeignKey('sellers.Seller', on_delete=models.PROTECT, null=True, blank=True, related_name='ledger_entries')
    courier = models.ForeignKey('logistics.DeliveryPartner', on_delete=models.PROTECT, null=True, blank=True, related_name='ledger_entries')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(amount__gt=0), name='ledger_entry_positive_amount')]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Ledger entries are immutable.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Ledger entries cannot be deleted.')


class EscrowFreeze(models.Model):
    """Funds isolated from release while a dispute is active."""
    STATUS_CHOICES = (('ACTIVE', 'Active'), ('RELEASED', 'Released'), ('REFUNDED', 'Refunded'))
    order = models.ForeignKey('orders.Order', on_delete=models.PROTECT, related_name='escrow_freezes')
    order_item = models.ForeignKey('orders.OrderItem', on_delete=models.PROTECT, null=True, blank=True, related_name='escrow_freezes')
    dispute = models.OneToOneField('disputes.Dispute', on_delete=models.PROTECT, related_name='escrow_freeze')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='ZMW')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)


class SellerPayoutRequest(models.Model):
    """MVP manual withdrawal queue exported weekly by administrators."""
    STATUS_CHOICES = (('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('EXPORTED', 'Exported'), ('PAID', 'Paid'), ('REJECTED', 'Rejected'))
    seller = models.ForeignKey('sellers.Seller', on_delete=models.PROTECT, related_name='payout_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    provider = models.CharField(max_length=20)
    account_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    provider_reference = models.CharField(max_length=150, blank=True)

    def clean(self):
        if self.amount <= 0:
            raise ValidationError('Payout amount must be positive.')
        if not self.seller.can_publish_products():
            raise ValidationError('Fully verified seller KYC and payout ownership are required.')
        escrow = getattr(self.seller, 'escrow_account', None)
        if not escrow or self.amount > escrow.available_balance:
            raise ValidationError('Insufficient available seller balance.')


class OrderFinancialSnapshot(models.Model):
    """
    Immutable financial record per order.
    
    Purpose: The truth about money, frozen in time
    
    Why Snapshot:
    - Prices change, but past orders don't
    - Commission rates change, but past orders don't
    - Disputes need exact numbers from order time
    - Refunds need original amounts
    
    Separation of Concerns:
    - Created atomically with order payment
    - Never edited, only status changes
    - Sellers query for their earnings
    - Platform queries for revenue
    - Couriers never see this
    
    Status Flow:
    - HELD: Order paid, money held
    - RELEASED: Delivery confirmed, money to seller escrow
    - REFUNDED: Dispute resolved, money back to buyer
    - PARTIAL_REFUND: Compromise resolution
    """
    STATUS_CHOICES = (
        ('HELD', 'Held in Escrow'),
        ('RELEASED', 'Released to Seller'),
        ('REFUNDED', 'Refunded to Buyer'),
        ('PARTIAL_REFUND', 'Partially Refunded'),
    )
    
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.PROTECT,
        related_name='financial_snapshot'
    )
    
    # Money breakdown (immutable after creation)
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Sum of all order items'
    )
    commission_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Platform commission (calculated from rules)'
    )
    seller_earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='What seller receives (subtotal - commission)'
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Delivery cost (goes to courier)'
    )
    platform_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Additional platform fees (processing, etc.)'
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='HELD'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Order Financial Snapshot'
        verbose_name_plural = 'Order Financial Snapshots'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order.id} - {self.status} - K{self.subtotal}"
    
    def release_to_sellers(self):
        """
        Release funds to seller escrow accounts.
        
        Called when buyer confirms delivery.
        Multi-seller orders split by OrderItem seller.
        """
        if self.status != 'HELD':
            raise ValidationError(f'Can only release HELD snapshots. Current: {self.status}')
        
        # Get all order items grouped by seller
        from django.db.models import Sum
        seller_totals = self.order.items.values('seller').annotate(
            item_total=Sum(models.F('price_snapshot') * models.F('quantity'))
        )
        
        for seller_data in seller_totals:
            seller_id = seller_data['seller']
            item_total = seller_data['item_total']
            
            # Calculate commission for this seller's items
            # (In real system, might vary by category)
            commission_rate = self.commission_amount / self.subtotal
            seller_commission = item_total * commission_rate
            seller_net = item_total - seller_commission
            
            # Add to seller's escrow pending balance
            from apps.sellers.models import Seller
            seller = Seller.objects.get(id=seller_id)
            escrow, _ = EscrowAccount.objects.get_or_create(seller=seller)
            escrow.add_pending(seller_net)
        
        self.status = 'RELEASED'
        self.released_at = timezone.now()
        self.save()
    
    def refund(self, partial_amount=None):
        """
        Process refund (dispute resolution or cancellation).
        
        Args:
            partial_amount: If provided, partial refund only
        """
        if self.status not in ['HELD', 'RELEASED']:
            raise ValidationError(f'Cannot refund from status: {self.status}')
        
        if partial_amount:
            if partial_amount <= 0 or partial_amount > self.subtotal:
                raise ValidationError('Invalid partial refund amount')
            self.status = 'PARTIAL_REFUND'
        else:
            self.status = 'REFUNDED'
        
        self.refunded_at = timezone.now()
        self.save()
        
        # If already released to sellers, deduct from their escrow
        if self.status == 'RELEASED':
            # TODO: Deduct from seller escrow accounts
            pass
    
    @classmethod
    def create_for_order(cls, order):
        """
        Generate financial snapshot for paid order.
        
        Called when order transitions to PAID status.
        """
        if hasattr(order, 'financial_snapshot'):
            raise ValidationError('Order already has financial snapshot')
        
        # Calculate totals
        subtotal = order.calculate_total()
        
        # Calculate weighted commission across all items
        total_commission = Decimal('0.00')
        for item in order.items.all():
            rate = CommissionRule.get_rate_for_product(item.product)
            item_commission = item.subtotal * (rate / Decimal('100.00'))
            total_commission += item_commission
        
        seller_earnings = subtotal - total_commission
        
        # Create snapshot
        snapshot = cls.objects.create(
            order=order,
            subtotal=subtotal,
            commission_amount=total_commission,
            seller_earnings=seller_earnings,
            delivery_fee=order.delivery_fee,
            platform_fee=Decimal('0.00'),
            status='HELD'
        )
        
        return snapshot
