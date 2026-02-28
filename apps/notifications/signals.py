"""
Notification Signals - Automatic notification triggers.

Purpose: Auto-create notifications when key events occur in the marketplace.

Design Philosophy:
- Decoupled: Models don't know about notifications
- Automatic: No manual notification.create() in views
- Consistent: All events trigger notifications the same way
- Scalable: Easy to add new notification triggers

Signal Types:
- post_save: After model saved (product approved, order paid)
- pre_save: Before model saved (status change detection)
- custom: Manual signals (seller verified)

Business Events That Trigger Notifications:
1. Product approved → Notify seller
2. Product suspended → Notify seller with reason
3. Order placed (PAID) → Notify seller
4. Order ready for delivery → Notify buyer
5. Order in transit → Notify buyer
6. Order delivered → Notify buyer and seller
7. Seller verified → Notify seller
8. Review left → Notify seller

Future: Email/SMS dispatch, push notifications to mobile app
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal
from apps.products.models import Product
from apps.orders.models import Order
from apps.sellers.models import Seller
from apps.reviews.models import Review
from apps.notifications.models import Notification


# Custom signal for seller verification
seller_verified = Signal()


@receiver(pre_save, sender=Product)
def detect_product_status_change(sender, instance, **kwargs):
    """
    Detect product status changes to trigger appropriate notifications.
    
    Why pre_save?
    - We need the old status to compare with new status
    - Can't do this in post_save (old value lost)
    
    Status Changes That Trigger Notifications:
    - PENDING_APPROVAL → ACTIVE (approved)
    - ACTIVE → SUSPENDED (violation)
    - DRAFT → PENDING_APPROVAL (submitted for review)
    """
    if instance.pk:  # Only for updates, not creates
        try:
            old_product = Product.objects.get(pk=instance.pk)
            
            # Store old status for post_save signal
            instance._old_status = old_product.status
        except Product.DoesNotExist:
            instance._old_status = None


@receiver(post_save, sender=Product)
def notify_product_status_change(sender, instance, created, **kwargs):
    """
    Send notifications when product status changes.
    
    Notifications:
    1. Product Approved: "Your product [name] is now live!"
    2. Product Suspended: "Your product [name] has been suspended"
    3. Product Submitted: "Your product [name] is under review"
    """
    if created:
        return  # Don't notify on creation (still DRAFT)
    
    # Get old status from pre_save signal
    old_status = getattr(instance, '_old_status', None)
    
    if old_status and old_status != instance.status:
        
        # Product Approved: PENDING_APPROVAL → ACTIVE
        if old_status == 'PENDING_APPROVAL' and instance.status == 'ACTIVE':
            Notification.objects.create(
                user=instance.seller.user,
                notification_type='PRODUCT',
                title='Product Approved',
                message=f'Your product "{instance.name}" has been approved and is now live!',
                related_id=instance.id
            )
        
        # Product Suspended: ACTIVE → SUSPENDED
        elif old_status == 'ACTIVE' and instance.status == 'SUSPENDED':
            Notification.objects.create(
                user=instance.seller.user,
                notification_type='PRODUCT',
                title='Product Suspended',
                message=f'Your product "{instance.name}" has been suspended. Please contact support.',
                related_id=instance.id
            )
        
        # Product Submitted: DRAFT → PENDING_APPROVAL
        elif old_status == 'DRAFT' and instance.status == 'PENDING_APPROVAL':
            Notification.objects.create(
                user=instance.seller.user,
                notification_type='PRODUCT',
                title='Product Under Review',
                message=f'Your product "{instance.name}" has been submitted for review. You\'ll be notified once approved.',
                related_id=instance.id
            )


@receiver(pre_save, sender=Order)
def detect_order_status_change(sender, instance, **kwargs):
    """
    Detect order status changes to trigger appropriate notifications.
    
    Status Changes That Trigger Notifications:
    - PENDING → PAID (payment received)
    - PAID → READY_FOR_DELIVERY (seller packed order)
    - READY_FOR_DELIVERY → IN_TRANSIT (on the way)
    - IN_TRANSIT → DELIVERED (arrived)
    """
    if instance.pk:  # Only for updates, not creates
        try:
            old_order = Order.objects.get(pk=instance.pk)
            instance._old_status = old_order.status
        except Order.DoesNotExist:
            instance._old_status = None


@receiver(post_save, sender=Order)
def notify_order_status_change(sender, instance, created, **kwargs):
    """
    Send notifications when order status changes.
    
    Notifications:
    1. Order Paid → Notify seller (new order alert)
    2. Ready for Delivery → Notify buyer (order being prepared)
    3. In Transit → Notify buyer (track your order)
    4. Delivered → Notify buyer (confirm receipt) and seller (payment release)
    """
    old_status = getattr(instance, '_old_status', None)
    
    if old_status and old_status != instance.status:
        
        # Order Paid: PENDING → PAID
        # Notify seller: You have a new order!
        if old_status == 'PENDING' and instance.status == 'PAID':
            # TODO: Get seller from OrderItem when implemented
            # For now, create a system notification
            Notification.objects.create(
                user=instance.buyer,
                notification_type='ORDER',
                title='Payment Confirmed',
                message=f'Your payment for Order #{instance.id} has been confirmed.',
                related_id=instance.id
            )
        
        # Ready for Delivery: PAID → READY_FOR_DELIVERY
        # Notify buyer: Your order is being prepared
        elif old_status == 'PAID' and instance.status == 'READY_FOR_DELIVERY':
            Notification.objects.create(
                user=instance.buyer,
                notification_type='ORDER',
                title='Order Being Prepared',
                message=f'Your Order #{instance.id} is being prepared for delivery.',
                related_id=instance.id
            )
        
        # In Transit: READY_FOR_DELIVERY → IN_TRANSIT
        # Notify buyer: Your order is on the way
        elif old_status == 'READY_FOR_DELIVERY' and instance.status == 'IN_TRANSIT':
            Notification.objects.create(
                user=instance.buyer,
                notification_type='DELIVERY',
                title='Order In Transit',
                message=f'Your Order #{instance.id} is on the way! Track delivery in the app.',
                related_id=instance.id
            )
        
        # Delivered: IN_TRANSIT → DELIVERED
        # Notify buyer: Confirm you received your order
        # Notify seller: Payment will be released
        elif old_status == 'IN_TRANSIT' and instance.status == 'DELIVERED':
            Notification.objects.create(
                user=instance.buyer,
                notification_type='DELIVERY',
                title='Order Delivered',
                message=f'Order #{instance.id} has been delivered. Please confirm receipt and leave a review!',
                related_id=instance.id
            )


@receiver(seller_verified)
def notify_seller_verified(sender, seller, **kwargs):
    """
    Notify seller when their account is verified.
    
    Custom signal: Triggered manually in admin action.
    
    Notification: "Your seller account has been verified! You can now list products."
    """
    Notification.objects.create(
        user=seller.user,
        notification_type='SELLER',
        title='Seller Account Verified',
        message='Congratulations! Your seller account has been verified. You can now list products on Optimistic.',
        related_id=seller.id
    )


@receiver(post_save, sender=Review)
def notify_review_left(sender, instance, created, **kwargs):
    """
    Notify seller when buyer leaves a review.
    
    Notification: "You received a [X] star review for [Product Name]"
    """
    if created:
        # Determine emoji based on rating
        rating_emoji = '⭐' * instance.rating
        
        Notification.objects.create(
            user=instance.seller.user,
            notification_type='PRODUCT',
            title='New Review Received',
            message=f'You received a {instance.rating}-star review for "{instance.product.name}": {rating_emoji}',
            related_id=instance.product.id
        )
