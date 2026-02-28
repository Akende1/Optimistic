"""
Async Task Boundaries - Celery-Ready Architecture

Purpose: Define what happens outside request/response cycle

This module documents async task contracts.
When Celery is added, these become @shared_task functions.
For now, they're sync functions that will be called async later.

Task Design Principles:
1. Idempotent: Running twice = same result
2. Atomic: All-or-nothing (no partial state)
3. Logged: Every execution recorded
4. Retryable: Failures don't corrupt state
5. Independent: No view/request context

Separation of Concerns:
- Tasks don't trust frontend triggers
- Tasks validate all inputs
- Tasks never assume success
- Tasks log outcomes
"""

from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ORDER TASKS
# ============================================================================

def auto_cancel_unpaid_orders():
    """
    Auto-cancel orders that remain PENDING beyond timeout.
    
    Schedule: Every 15 minutes
    Business Rule: PENDING orders older than 30 minutes auto-cancelled
    
    Why Async:
    - Runs on schedule, not user action
    - Prevents inventory lockup
    - May affect many orders at once
    
    When Celery:
        @shared_task
        @periodic_task(run_every=timedelta(minutes=15))
    """
    from apps.orders.models import Order
    
    timeout = timezone.now() - timezone.timedelta(minutes=30)
    pending_orders = Order.objects.filter(
        status='PENDING',
        created_at__lt=timeout
    )
    
    cancelled_count = 0
    for order in pending_orders:
        try:
            with transaction.atomic():
                order.status = 'CANCELLED'
                order.save()
                cancelled_count += 1
                logger.info(f"Auto-cancelled order #{order.pk}")
        except Exception as e:
            logger.error(f"Failed to cancel order #{order.pk}: {e}")
    
    logger.info(f"Auto-cancelled {cancelled_count} unpaid orders")
    return cancelled_count


def monitor_delivery_sla():
    """
    Monitor delivery SLA breaches and alert admin.
    
    Schedule: Every hour
    Business Rule: IN_TRANSIT orders older than 3 days flagged
    
    Why Async:
    - Runs periodically
    - Generates notifications
    - May check many deliveries
    
    When Celery:
        @shared_task
        @periodic_task(run_every=timedelta(hours=1))
    """
    from apps.orders.models import Order
    from apps.notifications.models import Notification
    
    sla_breach = timezone.now() - timezone.timedelta(days=3)
    overdue_orders = Order.objects.filter(
        status='IN_TRANSIT',
        updated_at__lt=sla_breach
    )
    
    for order in overdue_orders:
        # Create admin notification
        logger.warning(f"SLA breach: Order #{order.pk} in transit for >3 days")
        # TODO: Create admin notification
    
    return overdue_orders.count()


def calculate_order_totals(order_id):
    """
    Recalculate order total from OrderItems.
    
    Trigger: After OrderItem creation/update
    Business Rule: total_amount = sum(item.subtotal)
    
    Why Async:
    - Decouples cart → order logic
    - Can be retried if fails
    - Doesn't block checkout flow
    
    When Celery:
        @shared_task(bind=True, max_retries=3)
    """
    from apps.orders.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
        calculated_total = order.calculate_total()
        
        if order.total_amount != calculated_total:
            order.total_amount = Decimal(str(calculated_total))
            order.save()
            logger.info(f"Updated order #{order_id} total to {calculated_total}")
        
        return float(calculated_total)
    except Order.DoesNotExist:
        logger.error(f"Order #{order_id} not found for total calculation")
        return None


# ============================================================================
# FINANCIAL TASKS
# ============================================================================

def generate_financial_snapshot(order_id):
    """
    Generate OrderFinancialSnapshot when order paid.
    
    Trigger: Order status → PAID
    Business Rule: Snapshot created atomically with payment
    
    Why Async:
    - Complex calculation
    - Multiple database queries
    - Shouldn't block payment confirmation
    
    When Celery:
        @shared_task(bind=True, max_retries=3)
    """
    from apps.orders.models import Order
    from apps.finances.models import OrderFinancialSnapshot
    
    try:
        order = Order.objects.get(id=order_id)
        
        if hasattr(order, 'financial_snapshot'):
            logger.warning(f"Order #{order_id} already has snapshot")
            return None
        
        with transaction.atomic():
            snapshot = OrderFinancialSnapshot.create_for_order(order)
            logger.info(f"Created financial snapshot for order #{order_id}")
            return snapshot.pk
    
    except Order.DoesNotExist:
        logger.error(f"Order #{order_id} not found for snapshot")
        return None
    except Exception as e:
        logger.error(f"Failed to create snapshot for order #{order_id}: {e}")
        raise


def release_seller_funds(order_id):
    """
    Release funds from HELD → seller escrow when delivered.
    
    Trigger: Buyer confirms delivery
    Business Rule: Money moves from platform to seller escrow
    
    Why Async:
    - Financial operation (must be reliable)
    - May involve multiple sellers (multi-vendor order)
    - Audit logging required
    
    When Celery:
        @shared_task(bind=True, max_retries=5)
    """
    from apps.orders.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
        
        with transaction.atomic():
            from apps.finances.models import OrderFinancialSnapshot
            snapshot = OrderFinancialSnapshot.objects.filter(order=order).first()
            if not snapshot:
                logger.error(f"Order #{order_id} has no financial snapshot")
                return False
            
            snapshot.release_to_sellers()
            logger.info(f"Released funds for order #{order_id} to seller escrow")
            return True
    
    except Exception as e:
        logger.error(f"Failed to release funds for order #{order_id}: {e}")
        raise


def clear_courier_earnings():
    """
    Move courier earnings from PENDING → CLEARED.
    
    Schedule: Every 6 hours
    Business Rule: PENDING earnings with confirmed deliveries
    
    Why Async:
    - Batch operation
    - Affects multiple couriers
    - Financial ledger updates
    
    When Celery:
        @shared_task
        @periodic_task(run_every=timedelta(hours=6))
    """
    from apps.logistics.models import CourierEarning
    from apps.orders.models import Order
    
    # Find deliveries that are confirmed but earnings still pending
    pending_earnings = CourierEarning.objects.filter(
        status='PENDING',
        delivery__order__status='DELIVERED',
        delivery__order__confirmed_by_buyer=True
    )
    
    cleared_count = 0
    for earning in pending_earnings:
        try:
            with transaction.atomic():
                earning.mark_cleared()
                cleared_count += 1
                logger.info(f"Cleared earning #{earning.pk} for courier {earning.courier.name}")
        except Exception as e:
            logger.error(f"Failed to clear earning #{earning.pk}: {e}")
    
    logger.info(f"Cleared {cleared_count} courier earnings")
    return cleared_count


# ============================================================================
# NOTIFICATION TASKS
# ============================================================================

def send_order_status_notification(order_id, old_status, new_status):
    """
    Send notification when order status changes.
    
    Trigger: Order status update
    Business Rule: Notify buyer/seller of status changes
    
    Why Async:
    - Doesn't block order update
    - Email/SMS external services
    - Can retry on failure
    
    When Celery:
        @shared_task(bind=True, max_retries=3)
    """
    from apps.orders.models import Order
    from apps.notifications.models import Notification
    
    try:
        order = Order.objects.get(id=order_id)
        
        # Create notification for buyer
        Notification.objects.create(
            user=order.buyer,
            notification_type='ORDER_UPDATE',
            title=f'Order #{order.pk} Status Update',
            message=f'Your order status changed to {new_status}',
            link=f'/orders/{order.pk}/'
        )
        
        logger.info(f"Sent status notification for order #{order_id}: {old_status} → {new_status}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send notification for order #{order_id}: {e}")
        return False


def send_delivery_update(delivery_id):
    """
    Notify buyer of delivery status update.
    
    Trigger: Delivery status change
    Business Rule: Real-time tracking updates
    
    Why Async:
    - External notifications (SMS, push)
    - Non-blocking
    - Retryable
    
    When Celery:
        @shared_task(bind=True, max_retries=3)
    """
    from apps.logistics.models import Delivery
    
    try:
        delivery = Delivery.objects.get(id=delivery_id)
        order = delivery.order
        
        # Create notification for buyer
        logger.info(f"Sent delivery update for order #{order.id}")
        # TODO: Implement notification creation
        
        return True
    except Exception as e:
        logger.error(f"Failed to send delivery update #{delivery_id}: {e}")
        return False


# ============================================================================
# MAINTENANCE TASKS
# ============================================================================

def snapshot_daily_metrics():
    """
    Capture daily platform metrics for analytics.
    
    Schedule: Daily at midnight
    Business Rule: Store aggregated metrics for dashboard
    
    Why Async:
    - Expensive aggregations
    - Doesn't need to be real-time
    - Historical data preservation
    
    When Celery:
        @shared_task
        @periodic_task(run_every=crontab(hour=0, minute=0))
    """
    from django.db.models import Sum, Count
    from apps.orders.models import Order
    from apps.products.models import Product
    
    today = timezone.now().date()
    
    metrics = {
        'date': today,
        'total_orders': Order.objects.filter(created_at__date=today).count(),
        'completed_orders': Order.objects.filter(
            status='DELIVERED',
            delivered_at__date=today
        ).count(),
        'total_revenue': Order.objects.filter(
            status='DELIVERED',
            delivered_at__date=today
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'new_products': Product.objects.filter(created_at__date=today).count(),
    }
    
    logger.info(f"Daily metrics snapshot: {metrics}")
    # TODO: Store in DailyMetrics model
    
    return metrics


def alert_low_stock_products():
    """
    Alert sellers of low stock products.
    
    Schedule: Daily at 8 AM
    Business Rule: Notify when stock < 5 for ACTIVE products
    
    Why Async:
    - Batch operation
    - Multiple notifications
    - Not time-critical
    
    When Celery:
        @shared_task
        @periodic_task(run_every=crontab(hour=8, minute=0))
    """
    from apps.products.models import Product
    
    low_stock = Product.objects.filter(
        status='ACTIVE',
        stock__lt=5
    ).select_related('seller')
    
    alert_count = 0
    for product in low_stock:
        logger.warning(f"Low stock alert: {product.name} ({product.stock} remaining)")
        # TODO: Create notification for seller
        alert_count += 1
    
    logger.info(f"Sent {alert_count} low stock alerts")
    return alert_count


def detect_inactive_sellers():
    """
    Flag sellers with no activity for 30+ days.
    
    Schedule: Weekly
    Business Rule: Inactive = no orders or product updates in 30 days
    
    Why Async:
    - Complex query
    - Non-urgent
    - Batch operation
    
    When Celery:
        @shared_task
        @periodic_task(run_every=crontab(day_of_week=1, hour=9))
    """
    from apps.sellers.models import Seller
    
    threshold = timezone.now() - timezone.timedelta(days=30)
    
    inactive_sellers = Seller.objects.filter(
        verified=True,
        products__updated_at__lt=threshold
    ).distinct()
    
    logger.info(f"Found {inactive_sellers.count()} inactive sellers")
    # TODO: Create admin notification or email
    
    return inactive_sellers.count()


# ============================================================================
# TASK REGISTRY
# ============================================================================

# When Celery is added, this becomes:
# from celery import shared_task
# All functions above get @shared_task decorator

# Periodic tasks schedule (for Celery Beat):
PERIODIC_TASKS = {
    'auto-cancel-unpaid': {
        'task': 'apps.tasks.orders.auto_cancel_unpaid_orders',
        'schedule': 'every 15 minutes',
    },
    'monitor-delivery-sla': {
        'task': 'apps.tasks.orders.monitor_delivery_sla',
        'schedule': 'every 1 hour',
    },
    'clear-courier-earnings': {
        'task': 'apps.tasks.financial.clear_courier_earnings',
        'schedule': 'every 6 hours',
    },
    'daily-metrics': {
        'task': 'apps.tasks.maintenance.snapshot_daily_metrics',
        'schedule': 'daily at midnight',
    },
    'low-stock-alerts': {
        'task': 'apps.tasks.maintenance.alert_low_stock_products',
        'schedule': 'daily at 8 AM',
    },
    'inactive-sellers': {
        'task': 'apps.tasks.maintenance.detect_inactive_sellers',
        'schedule': 'weekly on Monday at 9 AM',
    },
}
