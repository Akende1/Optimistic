from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class RfqRequest(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('AWARDED', 'Awarded'),
        ('CLOSED', 'Closed'),
        ('EXPIRED', 'Expired'),
    )

    INCOTERM_CHOICES = (
        ('EXW', 'Ex Works'),
        ('FOB', 'Free On Board'),
        ('CIF', 'Cost Insurance Freight'),
        ('DDP', 'Delivered Duty Paid'),
        ('OTHER', 'Other'),
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rfq_requests',
    )
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', db_index=True)
    incoterm = models.CharField(max_length=12, choices=INCOTERM_CHOICES, default='OTHER')
    delivery_location = models.CharField(max_length=180, blank=True)
    is_sample_required = models.BooleanField(default=False)
    response_deadline = models.DateTimeField(db_index=True)
    desired_delivery_date = models.DateField(null=True, blank=True)
    awarded_quote = models.ForeignKey(
        'SupplierQuote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='awarded_rfqs',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'RFQ #{self.id} - {self.title}'

    def clean(self):
        super().clean()
        if self.response_deadline and self.response_deadline <= timezone.now():
            raise ValidationError('Response deadline must be in the future.')

    @property
    def is_open_for_quotes(self):
        return self.status == 'OPEN' and self.response_deadline >= timezone.now()


class RfqItem(models.Model):
    rfq = models.ForeignKey(RfqRequest, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rfq_items',
    )
    category = models.ForeignKey(
        'products.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rfq_items',
    )
    description = models.CharField(max_length=220)
    quantity = models.PositiveIntegerField(default=1)
    target_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=40, default='unit')

    class Meta:
        ordering = ['id']

    def clean(self):
        super().clean()
        if self.quantity <= 0:
            raise ValidationError('Quantity must be greater than zero.')
        if self.target_price is not None and self.target_price < Decimal('0.00'):
            raise ValidationError('Target price cannot be negative.')


class SupplierQuote(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('WON', 'Won'),
        ('LOST', 'Lost'),
        ('WITHDRAWN', 'Withdrawn'),
    )

    rfq = models.ForeignKey(RfqRequest, on_delete=models.CASCADE, related_name='quotes')
    seller = models.ForeignKey('sellers.Seller', on_delete=models.CASCADE, related_name='rfq_quotes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED', db_index=True)
    lead_time_days = models.PositiveIntegerField(default=7)
    notes = models.TextField(blank=True)
    valid_until = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        constraints = [
            models.UniqueConstraint(fields=['rfq', 'seller'], name='unique_quote_per_seller_per_rfq'),
        ]

    def __str__(self):
        return f'Quote #{self.id} for RFQ #{self.rfq_id}'


class SupplierQuoteItem(models.Model):
    quote = models.ForeignKey(SupplierQuote, on_delete=models.CASCADE, related_name='items')
    rfq_item = models.ForeignKey(RfqItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='quote_items')
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quote_items',
    )
    description = models.CharField(max_length=220)
    quantity = models.PositiveIntegerField(default=1)
    moq = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['id']

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
