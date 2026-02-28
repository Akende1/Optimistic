from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    System notifications - how the platform communicates with users.
    
    Design Principles:
    - Immutable: Once created, cannot be edited (audit trail)
    - Read-only flag: Users can mark as read, but message stays
    - Type-based: Different notification types for filtering
    - Reference tracking: Links to related objects (order, product, etc.)
    
    Notification Flow:
    1. System event happens (order placed, product approved, etc.)
    2. create_notification() is called
    3. Notification created with is_read=False
    4. User sees notification in their feed
    5. User clicks notification → is_read=True
    6. Notification remains in database forever (history)
    
    Why Not Delete Notifications?
    - Users may want to re-read old notifications
    - Provides audit trail of system communications
    - Can build analytics (notification effectiveness)
    - Disk space is cheap, user experience is expensive
    
    Future Enhancements:
    - Email notifications (send on create)
    - SMS notifications (for critical events)
    - Push notifications (mobile app)
    - Notification preferences (per type)
    """
    
    # Type categories: Groups notifications by context
    TYPE_CHOICES = (
        ('ORDER', 'Order'),       # Order placed, shipped, delivered
        ('PRODUCT', 'Product'),   # Product approved, suspended
        ('DELIVERY', 'Delivery'), # Delivery status updates
        ('SELLER', 'Seller'),     # Seller verified, rejected
        ('SYSTEM', 'System'),     # Platform announcements, maintenance
    )

    # Recipient: Who should see this notification?
    # CASCADE: If user deleted, their notifications deleted too
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # Notification content
    notification_type = models.CharField(
        max_length=10, 
        choices=TYPE_CHOICES,
        help_text="Category for filtering and icons",
        db_index=True
    )
    title = models.CharField(
        max_length=200,
        help_text="Short headline (shown in list)"
    )
    message = models.TextField(
        help_text="Full notification text (shown in detail)"
    )
    
    # Read tracking: Has user seen this?
    # False by default = new/unread notification
    is_read = models.BooleanField(
        default=False,
        help_text="User can mark as read via API",
        db_index=True
    )
    
    # Timestamp: When was this notification created?
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Optional link to related object (order #5, product #100, etc.)
    # Stored as ID because object type varies (polymorphic reference)
    # Frontend uses this + notification_type to build link
    related_id = models.IntegerField(
        null=True, 
        blank=True, 
        help_text='ID of related object (order, product, delivery, etc.)'
    )

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    @classmethod
    def create_notification(cls, user, notification_type, title, message, related_id=None):
        """Helper method to create notifications."""
        return cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_id=related_id
        )
