from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType


from apps.common.models import AuditLog


def _get_target_instance(resolution):
    """Helper to resolve dispute target from a resolution."""
    dispute = getattr(resolution, 'dispute_case', None)
    if not dispute:
        return None
    return dispute.target


class Dispute(models.Model):
    """
    Dispute tracking - the courtroom without emotion.
    
    Purpose: Formal conflict resolution between parties
    
    Dispute Targets:
    - Order (wrong items, not delivered)
    - OrderItem (defective product)
    - Delivery (damaged in transit)
    - Review (false/abusive review)
    
    Separation of Concerns:
    - Buyers/Sellers open disputes
    - Couriers can be implicated
    - Admin resolves disputes
    - System enforces outcomes
    - All evidence preserved
    
    Status Flow:
    - OPEN: Dispute filed
    - EVIDENCE: Parties submit evidence
    - UNDER_REVIEW: Admin reviewing
    - RESOLVED: Decision made
    - ESCALATED: Requires higher authority
    - CLOSED: Final, immutable
    """
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('EVIDENCE', 'Collecting Evidence'),
        ('UNDER_REVIEW', 'Under Admin Review'),
        ('RESOLVED', 'Resolved'),
        ('ESCALATED', 'Escalated'),
        ('CLOSED', 'Closed'),
    )
    
    REASON_CHOICES = (
        ('ITEM_NOT_RECEIVED', 'Item Not Received'),
        ('ITEM_DAMAGED', 'Item Damaged in Transit'),
        ('WRONG_ITEM', 'Wrong Item Received'),
        ('DEFECTIVE_PRODUCT', 'Defective/Broken Product'),
        ('MISSING_PARTS', 'Missing Parts/Items'),
        ('NOT_AS_DESCRIBED', 'Not As Described'),
        ('SELLER_UNRESPONSIVE', 'Seller Not Responding'),
        ('DELIVERY_DELAY', 'Excessive Delivery Delay'),
        ('FRAUDULENT_REVIEW', 'Fraudulent/Fake Review'),
        ('OTHER', 'Other (See Description)'),
    )
    
    # Who opened the dispute
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='opened_disputes'
    )
    
    # What is being disputed (polymorphic)
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text='Type of object being disputed (Order, OrderItem, Delivery, Review)'
    )
    target_object_id = models.PositiveIntegerField(
        help_text='ID of the disputed object'
    )
    target = GenericForeignKey('target_content_type', 'target_object_id')
    
    # Dispute details
    reason = models.CharField(
        max_length=30,
        choices=REASON_CHOICES
    )
    description = models.TextField(
        help_text='Detailed explanation of the issue'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN'
    )
    
    # Resolution
    resolution = models.OneToOneField(
        'DisputeResolution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispute_case'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    evidence_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Deadline for submitting evidence'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Dispute'
        verbose_name_plural = 'Disputes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['target_content_type', 'target_object_id']),
        ]
    
    def __str__(self) -> str:
        return f"Dispute #{self.pk or 'New'} - {self.reason} ({self.status})"
    
    def open_evidence_window(self, days=3):
        """Open evidence collection period."""
        if self.status != 'OPEN':
            raise ValidationError(f'Can only open evidence for OPEN disputes. Current: {self.status}')
        
        self.status = 'EVIDENCE'
        self.evidence_deadline = timezone.now() + timezone.timedelta(days=days)
        self.save()
    
    def submit_for_review(self):
        """Move to admin review."""
        if self.status not in ['OPEN', 'EVIDENCE']:
            raise ValidationError(f'Invalid transition to UNDER_REVIEW from {self.status}')
        
        self.status = 'UNDER_REVIEW'
        self.save()
    
    def resolve(self, resolution):
        """Attach resolution and mark as resolved."""
        if self.status not in ['UNDER_REVIEW', 'ESCALATED']:
            raise ValidationError(f'Can only resolve disputes UNDER_REVIEW or ESCALATED. Current: {self.status}')
        
        self.resolution = resolution
        self.status = 'RESOLVED'
        self.resolved_at = timezone.now()
        self.save()
    
    def close(self):
        """
        Close dispute permanently (immutable state).
        
        Called after resolution actions completed.
        """
        if self.status != 'RESOLVED':
            raise ValidationError('Can only close RESOLVED disputes')
        
        self.status = 'CLOSED'
        self.closed_at = timezone.now()
        self.save()
    
    def lock_target(self):
        """
        Lock disputed entity from modifications.
        
        Prevents parties from altering evidence.
        """
        # Implementation depends on target type
        # For now, mark dispute as active on target
        pass


class DisputeEvidence(models.Model):
    """
    Evidence submissions for disputes.
    
    Purpose: Collect proof from all parties
    
    Evidence Types:
    - Photos (damaged goods, delivery proof)
    - Screenshots (conversations, payment confirmations)
    - Documents (invoices, receipts)
    - Text notes (explanations, timelines)
    
    Rules:
    - All parties can submit
    - Evidence timestamped
    - Cannot delete after submission
    - Admin sees all evidence
    """
    EVIDENCE_TYPE_CHOICES = (
        ('PHOTO', 'Photo/Image'),
        ('DOCUMENT', 'Document/PDF'),
        ('TEXT', 'Text Note'),
        ('VIDEO', 'Video'),
        ('AUDIO', 'Audio Recording'),
    )
    
    dispute = models.ForeignKey(
        'Dispute',
        on_delete=models.CASCADE,
        related_name='evidence'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='submitted_evidence'
    )
    evidence_type = models.CharField(
        max_length=20,
        choices=EVIDENCE_TYPE_CHOICES
    )
    file = models.FileField(
        upload_to='disputes/evidence/',
        null=True,
        blank=True,
        help_text='Evidence file (photo, document, etc.)'
    )
    note = models.TextField(
        blank=True,
        help_text='Text explanation or context'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Dispute Evidence'
        verbose_name_plural = 'Dispute Evidence'
        ordering = ['submitted_at']
    
    def __str__(self):
        return f"Evidence for Dispute #{self.dispute.id} by {self.uploaded_by.username}"
    
    def clean(self):
        """Validate evidence submission."""
        # Check if dispute is still accepting evidence
        if self.dispute.status not in ['OPEN', 'EVIDENCE']:
            raise ValidationError('Dispute is no longer accepting evidence')
        
        # Check evidence deadline
        if self.dispute.evidence_deadline and timezone.now() > self.dispute.evidence_deadline:
            raise ValidationError('Evidence submission deadline has passed')
        
        # File required for non-text evidence
        if self.evidence_type != 'TEXT' and not self.file:
            raise ValidationError(f'{self.evidence_type} requires a file upload')


class DisputeResolution(models.Model):
    """
    Dispute resolution outcome - the verdict.
    
    Purpose: Record admin decision and enforce actions
    
    Outcomes:
    - Buyer refunded (full/partial)
    - Seller compensated
    - Courier penalized
    - No action (dispute rejected)
    
    Financial Actions:
    - REFUND_FULL: 100% to buyer
    - REFUND_PARTIAL: Percentage to buyer
    - SELLER_PENALTY: Deduct from escrow
    - COURIER_PENALTY: Deduct from wallet
    - NONE: No financial change
    
    Immutability:
    - Once saved, cannot edit
    - All financial actions logged
    - Appeals handled as new disputes
    """
    OUTCOME_CHOICES = (
        ('BUYER_FAVOR', 'Resolved in Buyer Favor'),
        ('SELLER_FAVOR', 'Resolved in Seller Favor'),
        ('PARTIAL_BUYER', 'Partial Resolution - Buyer'),
        ('PARTIAL_SELLER', 'Partial Resolution - Seller'),
        ('NO_FAULT', 'No Fault Found'),
        ('COURIER_FAULT', 'Courier at Fault'),
    )
    
    FINANCIAL_ACTION_CHOICES = (
        ('REFUND_FULL', 'Full Refund to Buyer'),
        ('REFUND_PARTIAL', 'Partial Refund to Buyer'),
        ('SELLER_PENALTY', 'Penalty to Seller'),
        ('COURIER_PENALTY', 'Penalty to Courier'),
        ('NONE', 'No Financial Action'),
    )
    
    outcome = models.CharField(
        max_length=20,
        choices=OUTCOME_CHOICES
    )
    financial_action = models.CharField(
        max_length=20,
        choices=FINANCIAL_ACTION_CHOICES,
        default='NONE'
    )
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Amount to refund (if applicable)'
    )
    penalty_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Penalty amount (if applicable)'
    )
    
    # Admin details
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='resolved_disputes'
    )
    resolution_notes = models.TextField(
        help_text='Admin explanation of decision'
    )
    
    # Actions taken
    actions_completed = models.BooleanField(
        default=False,
        help_text='All financial/system actions executed'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    actions_completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Dispute Resolution'
        verbose_name_plural = 'Dispute Resolutions'
    
    def __str__(self) -> str:
        return f"Resolution: {self.outcome}"
    
    def execute_financial_actions(self):
        """
        Execute financial actions (refunds, penalties).
        
        This is where money actually moves.
        """
        if self.actions_completed:
            raise ValidationError('Actions already completed')
        
        # Resolve actions against the disputed target when possible
        target = _get_target_instance(self)

        try:
            # Refunds
            if self.financial_action in ('REFUND_FULL', 'REFUND_PARTIAL'):
                # Target should be an Order or OrderItem
                from apps.finances.models import OrderFinancialSnapshot

                if not target:
                    raise ValidationError('No dispute target available for refund')

                # Get the order for the target
                order = None
                if hasattr(target, 'financial_snapshot') and getattr(target, 'financial_snapshot'):
                    snapshot = target.financial_snapshot
                elif hasattr(target, 'order'):
                    order = target.order
                    snapshot = getattr(order, 'financial_snapshot', None)
                elif target.__class__.__name__ == 'Order':
                    order = target
                    snapshot = getattr(order, 'financial_snapshot', None)
                else:
                    snapshot = None

                if not snapshot:
                    raise ValidationError('Order financial snapshot not found for refund')

                # Partial vs full
                if self.financial_action == 'REFUND_PARTIAL' and self.refund_amount:
                    snapshot.refund(partial_amount=self.refund_amount)
                else:
                    snapshot.refund()

                # Audit
                AuditLog.objects.create(
                    actor=self.resolved_by,
                    action='DISPUTE_RESOLVE_BUYER',
                    target_type='Order',
                    target_id=snapshot.order.id,
                    details={'refund_amount': str(self.refund_amount or snapshot.subtotal)},
                    ip_address='',
                )

            # Seller penalty
            elif self.financial_action == 'SELLER_PENALTY':
                if not self.penalty_amount:
                    raise ValidationError('Penalty amount required')

                # Try to find seller on the disputed target
                seller = None
                if target and hasattr(target, 'seller'):
                    seller = target.seller
                elif target and hasattr(target, 'order'):
                    # pick first seller from order items when ambiguous
                    try:
                        seller = target.order.items.first().seller
                    except Exception:
                        seller = None

                if not seller:
                    raise ValidationError('Seller not found for penalty')

                from apps.finances.models import EscrowAccount
                escrow, _ = EscrowAccount.objects.get_or_create(seller=seller)
                escrow.deduct_available(self.penalty_amount)

                AuditLog.objects.create(
                    actor=self.resolved_by,
                    action='DISPUTE_RESOLVE_SELLER',
                    target_type='Seller',
                    target_id=seller.id,
                    details={'penalty_amount': str(self.penalty_amount)},
                    ip_address='',
                )

            # Courier penalty
            elif self.financial_action == 'COURIER_PENALTY':
                if not self.penalty_amount:
                    raise ValidationError('Penalty amount required')

                courier = None
                if target and target.__class__.__name__ == 'Delivery':
                    courier = getattr(target, 'courier', None)

                if not courier:
                    raise ValidationError('Courier not found for penalty')

                from apps.logistics.models import CourierWallet
                wallet, _ = CourierWallet.objects.get_or_create(courier=courier)
                wallet.deduct_available(self.penalty_amount)

                AuditLog.objects.create(
                    actor=self.resolved_by,
                    action='DISPUTE_RESOLVE_SELLER',
                    target_type='DeliveryPartner',
                    target_id=courier.id,
                    details={'penalty_amount': str(self.penalty_amount)},
                    ip_address='',
                )

            # Mark completed
            self.actions_completed = True
            self.actions_completed_at = timezone.now()
            self.save()

        except Exception as exc:
            # Create audit entry for failure and raise to surface to caller
            try:
                AuditLog.objects.create(
                    actor=self.resolved_by,
                    action='ORDER_OVERRIDE',
                    target_type='DisputeResolution',
                    target_id=getattr(self, 'id', 0) or 0,
                    details={'error': str(exc)},
                    ip_address='',
                )
            except Exception:
                pass
            raise
    
    def clean(self):
        """Validate resolution data."""
        if self.financial_action in ['REFUND_FULL', 'REFUND_PARTIAL'] and not self.refund_amount:
            raise ValidationError('Refund amount required for refund actions')
        
        if self.financial_action in ['SELLER_PENALTY', 'COURIER_PENALTY'] and not self.penalty_amount:
            raise ValidationError('Penalty amount required for penalty actions')
