from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """
    Custom manager that excludes soft-deleted objects by default.
    
    Usage:
        Order.objects.all()  # Excludes deleted
        Order.all_objects.all()  # Includes deleted
        Order.objects.deleted()  # Only deleted
    """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def deleted(self):
        """Return only soft-deleted objects."""
        return super().get_queryset().filter(deleted_at__isnull=False)
    
    def with_deleted(self):
        """Return all objects including soft-deleted."""
        return super().get_queryset()


class Order(models.Model):
    """
    Order tracking - the transaction record.
    
    Purpose: Track buyer purchases from creation to completion
    
    Order Lifecycle:
    1. Buyer adds products to cart (frontend state)
    2. Buyer clicks 'Checkout' → Order created (status=PENDING)
    3. Buyer pays via mobile money → status=PAID
    4. Seller prepares order → status=READY_FOR_DELIVERY
    5. Courier picks up → status=IN_TRANSIT
    6. Buyer confirms → status=DELIVERED
    7. If cancelled → status=CANCELLED
    
    State Machine Rules:
    - PENDING → PAID (payment success)
    - PENDING → CANCELLED (buyer cancels before payment)
    - PAID → READY_FOR_DELIVERY (seller confirms)
    - PAID → CANCELLED (buyer/admin cancels after payment)
    - READY_FOR_DELIVERY → IN_TRANSIT (courier picks up)
    - IN_TRANSIT → DELIVERED (buyer confirms or auto-confirm)
    - No backwards transitions allowed
    - No skipping states (except cancellation)
    
    Business Rules:
    - One buyer per order (buyer FK)
    - Total amount calculated from OrderItems
    - Orders never deleted (only cancelled)
    - Status drives delivery workflow
    - Stock locked on PAID status
    - Review unlocked on DELIVERED status
    
    Why total_amount field?
    - Quick access without joining OrderItems
    - Historical record if prices change
    - Prevents manipulation after order placed
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),              # Created, awaiting payment
        ('PAID', 'Paid'),                    # Payment successful
        ('READY_FOR_DELIVERY', 'Ready for Delivery'),  # Seller confirmed fulfillment
        ('IN_TRANSIT', 'In Transit'),        # Delivery partner assigned, on the way
        ('DELIVERED', 'Delivered'),          # Buyer confirmed receipt or auto-confirmed
        ('CANCELLED', 'Cancelled'),          # User/system cancelled
    )
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        'PENDING': ['PAID', 'CANCELLED'],
        'PAID': ['READY_FOR_DELIVERY', 'CANCELLED'],
        'READY_FOR_DELIVERY': ['IN_TRANSIT'],
        'IN_TRANSIT': ['DELIVERED'],
        'DELIVERED': [],  # Terminal state
        'CANCELLED': [],  # Terminal state
    }

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    
    # Delivery & Location Fields
    shipping_address = models.TextField(help_text='Full delivery address')
    delivery_zone = models.CharField(
        max_length=100, 
        blank=True,
        help_text='e.g., Lusaka CBD, Kitwe Riverside, Ndola Town Center'
    )
    delivery_instructions = models.TextField(
        blank=True,
        help_text='Special delivery instructions (gate code, landmarks, etc.)'
    )
    
    # Delivery Partner Assignment
    delivery_partner = models.ForeignKey(
        'logistics.DeliveryPartner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders',
        help_text='Assigned courier/rider for delivery'
    )
    
    # Delivery Confirmation
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when order was delivered'
    )
    confirmed_by_buyer = models.BooleanField(
        default=False,
        help_text='Buyer has confirmed receiving the order'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Soft delete timestamp (order never truly deleted for audit trail)'
    )
    
    # Managers
    objects = SoftDeleteManager()  # Default: excludes deleted
    all_objects = models.Manager()  # Includes deleted

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.buyer.username} - {self.get_status_display()}"
    
    def _validate_transition(self, new_status):
        """
        Validate status transition before saving.
        
        Raises ValidationError if transition is invalid.
        """
        if self.pk and self.status != new_status:  # Only check on updates with status change
            valid_next_states = self.VALID_TRANSITIONS.get(self.status, [])
            if new_status not in valid_next_states:
                raise ValidationError(
                    f"Invalid status transition from {self.status} to {new_status}. "
                    f"Valid transitions: {', '.join(valid_next_states) if valid_next_states else 'None (terminal state)'}"
                )
    
    def save(self, *args, **kwargs):
        """Override save to validate state transitions."""
        if self.pk:  # Only validate on updates
            old_instance = Order.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                self._validate_transition(self.status)
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """Calculate order total from OrderItems."""
        total = sum(item.subtotal for item in self.items.all())
        return total
    
    def mark_as_paid(self):
        """
        Payment gateway callback: Mark order as paid.
        
        Transition: PENDING → PAID
        
        Business Rules:
        1. Deduct inventory from products (when OrderItem implemented)
        2. Trigger notification to seller (new order alert)
        3. Create delivery record
        
        Critical: This is where inventory locks happen!
        """
        if self.status != 'PENDING':
            raise ValidationError(f'Can only mark PENDING orders as paid. Current status: {self.status}')
        
        # TODO: Deduct inventory when OrderItem model is implemented
        # for item in self.items.all():
        #     product = item.product
        #     if product.stock < item.quantity:
        #         raise ValidationError(f'Insufficient stock for {product.name}')
        #     product.stock -= item.quantity
        #     product.save()
        
        self.status = 'PAID'
        self.save()
    
    def mark_ready_for_delivery(self):
        """
        Seller action: Confirm order is packed and ready for pickup.
        
        Transition: PAID → READY_FOR_DELIVERY
        
        Business Rules:
        1. Only seller can mark as ready
        2. Trigger notification to delivery partner (if assigned)
        3. Trigger notification to buyer (order being prepared)
        """
        if self.status != 'PAID':
            raise ValidationError(f'Can only mark PAID orders as ready. Current status: {self.status}')
        
        self.status = 'READY_FOR_DELIVERY'
        self.save()
    
    def mark_in_transit(self):
        """
        Delivery partner action: Order picked up and in transit.
        
        Transition: READY_FOR_DELIVERY → IN_TRANSIT
        
        Business Rules:
        1. Delivery partner must be assigned
        2. Trigger notification to buyer (track your order)
        """
        if self.status != 'READY_FOR_DELIVERY':
            raise ValidationError(f'Can only mark READY orders as in transit. Current status: {self.status}')
        
        self.status = 'IN_TRANSIT'
        self.save()
    
    def mark_delivered(self, confirmed_by_buyer=False):
        """
        Buyer/System action: Confirm order delivered.
        
        Transition: IN_TRANSIT → DELIVERED
        
        Business Rules:
        1. Release funds from escrow to seller
        2. Allow buyer to leave review
        3. If not confirmed after N days, auto-confirm
        4. Trigger notification to seller (payment on the way)
        """
        if self.status != 'IN_TRANSIT':
            raise ValidationError(f'Can only mark IN_TRANSIT orders as delivered. Current status: {self.status}')
        
        self.status = 'DELIVERED'
        self.delivery_confirmed_at = timezone.now()
        self.save()


class OrderItem(models.Model):
    """
    Order line items - linking orders to products with sellers.
    
    Purpose: Enable multi-seller marketplace orders
    
    Why This Model?
    - One order can contain products from multiple sellers
    - Tracks which seller owns each item
    - Captures price at time of order (prevents manipulation)
    - Enables per-seller fulfillment tracking
    - Foundation for commission calculation
    
    Business Rules:
    - price_snapshot = immutable price at checkout
    - seller = product.seller at time of order (cached for historical accuracy)
    - quantity validated against product.stock before order creation
    - Cannot modify after order is PAID
    
    Separation of Concerns:
    - Buyers see all items in their order
    - Sellers see only their items (queryset filtered by seller)
    - Admin sees everything
    - Couriers never see this model
    
    Commission Flow (Future):
    - OrderItem.subtotal = price_snapshot * quantity
    - Platform commission = subtotal * commission_rate
    - Seller payout = subtotal - platform_commission
    """
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Parent order containing this item'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,  # Cannot delete product with existing order items
        related_name='order_items',
        help_text='Product being purchased'
    )
    seller = models.ForeignKey(
        'sellers.Seller',
        on_delete=models.PROTECT,  # Cannot delete seller with existing order items
        related_name='order_items',
        help_text='Seller who owns this product (cached from product.seller)'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text='Number of units ordered'
    )
    price_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Price per unit at time of order (immutable)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Soft delete timestamp (preserves order history)'
    )
    
    # Managers
    objects = SoftDeleteManager()  # Default: excludes deleted
    all_objects = models.Manager()  # Includes deleted
    
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['order', 'seller']),  # Fast seller-specific queries
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f"Order #{self.order.id} - {self.product.name} x{self.quantity}"
    
    @property
    def subtotal(self):
        """Calculate line item subtotal (price × quantity)."""
        return self.price_snapshot * Decimal(self.quantity)
    
    def clean(self):
        """Validate order item before saving."""
        super().clean()
        
        # Ensure seller matches product seller at time of order
        if self.product and self.seller and self.product.seller != self.seller:
            raise ValidationError('Seller must match product seller')
        
        # Validate quantity
        if self.quantity <= 0:
            raise ValidationError('Quantity must be positive')
    
    def save(self, *args, **kwargs):
        """Auto-populate seller and price_snapshot on first save."""
        if not self.pk:  # Only on creation
            # Auto-set seller from product
            if self.product and not self.seller:
                self.seller = self.product.seller
            
            # Auto-set price from product (snapshot)
            if self.product and not self.price_snapshot:
                self.price_snapshot = self.product.price
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def cancel(self, reason=''):
        """
        Buyer/Admin action: Cancel order.
        
        Transition: PENDING or PAID → CANCELLED
        
        Business Rules:
        1. Can only cancel PENDING or PAID orders
        2. Cannot cancel if IN_TRANSIT or DELIVERED
        3. Restore inventory (when OrderItem implemented)
        4. Refund payment (when payment gateway integrated)
        5. Trigger notification to seller
        
        Args:
            reason (str): Why order was cancelled
        """
        if self.status not in ['PENDING', 'PAID']:
            raise ValidationError(f'Can only cancel PENDING or PAID orders. Current status: {self.status}')
        
        # TODO: Restore inventory when OrderItem model is implemented
        # if self.status == 'PAID':
        #     for item in self.items.all():
        #         product = item.product
        #         product.stock += item.quantity
        #         product.save()
        
        self.status = 'CANCELLED'
        self.save()
    
    def can_review(self):
        """
        Check if buyer can leave review.
        
        Rule: Can only review DELIVERED orders.
        """
        return self.status == 'DELIVERED'
    
    def can_cancel(self):
        """
        Check if order can be cancelled.
        
        Rule: Can only cancel PENDING or PAID orders.
        """
        return self.status in ['PENDING', 'PAID']
    
    def soft_delete(self):
        """
        Soft delete order (mark as deleted without removing from database).
        
        Use Case: Admin removes fraudulent orders while preserving audit trail
        Rule: Only CANCELLED orders can be soft deleted
        """
        if self.status != 'CANCELLED':
            raise ValidationError('Can only soft delete CANCELLED orders')
        
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        """Restore soft-deleted order."""
        self.deleted_at = None
        self.save()
