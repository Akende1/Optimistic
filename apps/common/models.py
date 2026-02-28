from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """
    Immutable audit trail - every admin action logged.
    
    Design Principles:
    - Append-only (no updates, no deletes)
    - Admin accountability (who did what, when, why)
    - Financial transparency (escrow movements)
    - Dispute resolution trail (decision history)
    - System configuration changes (settings, rules)
    
    Why Immutable?
    - Prevents evidence tampering
    - Legal compliance (transaction records)
    - Trust building (users can see transparency)
    - Fraud investigation (trace actor patterns)
    
    What Gets Logged:
    - User suspension/reinstatement
    - Escrow freeze/release
    - Dispute resolutions
    - Product approvals/flagging
    - Settings changes
    - Manual overrides
    """
    
    ACTION_CHOICES = (
        # User Management
        ('USER_SUSPEND', 'User Suspended'),
        ('USER_REINSTATE', 'User Reinstated'),
        ('USER_TERMINATE', 'User Terminated'),
        
        # Escrow Management
        ('ESCROW_FREEZE', 'Escrow Frozen'),
        ('ESCROW_RELEASE', 'Escrow Released'),
        ('ESCROW_MANUAL_RELEASE', 'Manual Escrow Release'),
        
        # Dispute Resolution
        ('DISPUTE_RESOLVE_BUYER', 'Dispute Resolved - Buyer Favor'),
        ('DISPUTE_RESOLVE_SELLER', 'Dispute Resolved - Seller Favor'),
        ('DISPUTE_RESOLVE_SPLIT', 'Dispute Resolved - Split Decision'),
        
        # Product Moderation
        ('PRODUCT_APPROVE', 'Product Approved'),
        ('PRODUCT_FLAG', 'Product Flagged'),
        ('PRODUCT_REMOVE', 'Product Removed'),
        
        # Order Management
        ('ORDER_OVERRIDE', 'Order Status Override'),
        ('ORDER_CANCEL_ADMIN', 'Order Cancelled by Admin'),
        
        # System Configuration
        ('SETTINGS_CHANGE', 'System Settings Changed'),
        ('RULE_CHANGE', 'Business Rule Changed'),
    )
    
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # Never delete admin who did action
        related_name='audit_actions',
        help_text='Admin who performed this action'
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text='What action was performed'
    )
    
    target_type = models.CharField(
        max_length=50,
        help_text='Model name of target (User, Order, Product, etc.)'
    )
    
    target_id = models.IntegerField(
        help_text='Primary key of target object'
    )
    
    details = models.JSONField(
        help_text='Additional context (reason, amounts, old/new values)'
    )
    
    ip_address = models.GenericIPAddressField(
        help_text='IP address of admin performing action'
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When action was performed (UTC)'
    )
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['actor', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['target_type', 'target_id']),
        ]
        # CRITICAL: No update or delete permissions
        permissions = [
            ('view_audit_logs', 'Can view audit logs'),
        ]
    
    def __str__(self) -> str:
        action_display = dict(self.ACTION_CHOICES).get(self.action, self.action)
        return f"{self.actor.username} - {action_display} - {self.timestamp}"
    
    def save(self, *args, **kwargs):
        # Only allow creation, never updates
        if self.pk:
            raise ValueError('Audit logs cannot be modified')
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Prevent deletion
        raise ValueError('Audit logs cannot be deleted')
