"""Transactional application services for commerce commands.

HTTP views, scheduled jobs, and future message consumers must call these services
instead of mutating order, stock, fulfillment, or payment states directly.
"""
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction, models
from decimal import Decimal
from django.utils import timezone

from apps.products.models import Product
from .models import InventoryReservation, Order, OrderFulfillment, PaymentAttempt, PaymentEvent


@transaction.atomic
def create_payment_attempt(*, order, provider, idempotency_key):
    """Create or return the caller's replay-safe payment attempt."""
    existing = PaymentAttempt.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        if existing.order_id != order.id or existing.amount != order.total_amount:
            raise ValidationError('Idempotency key was already used for a different payment.')
        return existing, False
    if order.status != 'PENDING':
        raise ValidationError('Payment attempts require a pending order.')
    if not order.reservations.filter(status='ACTIVE', expires_at__gt=timezone.now()).exists():
        raise ValidationError('The inventory reservation has expired.')
    return PaymentAttempt.objects.create(
        order=order, provider=provider, idempotency_key=idempotency_key,
        amount=order.total_amount, currency=order.currency,
    ), True


@transaction.atomic
def record_verified_payment_event(*, attempt_id, provider, external_event_id, event_type, payload):
    """Apply a provider event once after the adapter verifies its signature."""
    attempt = PaymentAttempt.objects.select_for_update().select_related('order').get(pk=attempt_id)
    existing = PaymentEvent.objects.filter(provider=provider, external_event_id=external_event_id).first()
    if existing:
        return existing, False
    try:
        # The inner savepoint keeps the outer transaction usable if two workers
        # race to insert the same provider event.
        with transaction.atomic():
            event = PaymentEvent.objects.create(
                attempt=attempt, provider=provider, external_event_id=external_event_id,
                event_type=event_type, payload=payload,
            )
    except IntegrityError:
        return PaymentEvent.objects.get(provider=provider, external_event_id=external_event_id), False

    if provider != attempt.provider:
        raise ValidationError('Payment provider does not match the attempt.')
    if event_type == 'payment.captured':
        amount = str(payload.get('amount', ''))
        currency = payload.get('currency')
        if amount != str(attempt.amount) or currency != attempt.currency:
            raise ValidationError('Captured payment amount or currency does not match the order.')
        attempt.order.mark_as_paid()
        from apps.finances.services import post_payment_capture
        post_payment_capture(attempt)
        from apps.common.outbox import enqueue
        enqueue(
            topic='notification.order_status', aggregate_type='Order', aggregate_id=attempt.order_id,
            idempotency_key=f'order-paid-notification:{attempt.order_id}',
            payload={'user_id': attempt.order.buyer_id, 'title': f'Order #{attempt.order_id} paid',
                     'message': 'Payment was confirmed and your order is awaiting fulfillment.'},
        )
        attempt.status = 'CAPTURED'
        attempt.provider_reference = str(payload.get('payment_reference', ''))
        attempt.save(update_fields=['status', 'provider_reference', 'updated_at'])
    elif event_type == 'payment.failed':
        attempt.status = 'FAILED'
        attempt.failure_code = str(payload.get('failure_code', ''))
        attempt.save(update_fields=['status', 'failure_code', 'updated_at'])
    return event, True


def simulate_payment_event(*, attempt, outcome, external_event_id):
    """Generate a deterministic development event through the real event path."""
    if outcome not in {'CAPTURED', 'FAILED'}:
        raise ValidationError('Simulation outcome must be CAPTURED or FAILED.')
    payload = {
        'amount': str(attempt.amount),
        'currency': attempt.currency,
        'payment_reference': f'SIM-{attempt.id}',
    }
    if outcome == 'FAILED':
        payload['failure_code'] = 'SIMULATED_FAILURE'
    return record_verified_payment_event(
        attempt_id=attempt.id,
        provider=attempt.provider,
        external_event_id=external_event_id,
        event_type='payment.captured' if outcome == 'CAPTURED' else 'payment.failed',
        payload=payload,
    )


@transaction.atomic
def expire_inventory_reservations(now=None):
    """Release expired checkout holds; safe to invoke repeatedly."""
    now = now or timezone.now()
    reservations = list(
        InventoryReservation.objects.select_for_update().filter(status='ACTIVE', expires_at__lte=now)
    )
    product_ids = {reservation.product_id for reservation in reservations}
    products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)}
    order_ids = set()
    for reservation in reservations:
        product = products[reservation.product_id]
        product.reserved_stock -= reservation.quantity
        product.save(update_fields=['reserved_stock', 'updated_at'])
        reservation.status = 'EXPIRED'
        reservation.save(update_fields=['status', 'updated_at'])
        order_ids.add(reservation.order_id)
    Order.objects.filter(id__in=order_ids, status='PENDING').update(status='EXPIRED', updated_at=now)
    return len(reservations)


FULFILLMENT_TRANSITIONS = {
    'AWAITING_ACCEPTANCE': {'ACCEPTED', 'REJECTED'},
    'ACCEPTED': {'PICKING', 'PACKED', 'CANCELLED'},
    'PICKING': {'PACKED', 'CANCELLED'},
    'PACKED': {'READY_FOR_PICKUP'},
    'READY_FOR_PICKUP': {'HANDED_OVER'},
}


@transaction.atomic
def transition_fulfillment(*, fulfillment, seller, new_status, carrier='', tracking_number=''):
    """Transition only the authenticated seller's fulfillment aggregate."""
    locked = OrderFulfillment.objects.select_for_update().select_related('order').get(pk=fulfillment.pk)
    if not seller.can_publish_products():
        raise ValidationError('Seller KYC verification is required for fulfillment actions.')
    if locked.seller_id != seller.id:
        raise ValidationError('You do not own this fulfillment.')
    if new_status not in FULFILLMENT_TRANSITIONS.get(locked.status, set()):
        raise ValidationError(f'Invalid fulfillment transition: {locked.status} -> {new_status}')
    if new_status == 'HANDED_OVER' and (not carrier or not tracking_number):
        raise ValidationError('Carrier and tracking number are required at handover.')
    locked.status = new_status
    if new_status == 'ACCEPTED':
        locked.accepted_at = timezone.now()
    elif new_status == 'READY_FOR_PICKUP':
        locked.ready_at = timezone.now()
    elif new_status == 'HANDED_OVER':
        locked.handed_over_at = timezone.now()
        locked.carrier, locked.tracking_number = carrier, tracking_number
    locked.save()
    order = locked.order
    if order.status == 'PAID' and not order.fulfillments.exclude(status='READY_FOR_PICKUP').exists():
        order.mark_ready_for_delivery()
    return locked


@transaction.atomic
def cancel_order_line(*, order_item, actor, quantity, reason):
    """Cancel/refund part or all of an order line without altering its snapshots."""
    from apps.finances.services import post_refund
    locked_order = Order.objects.select_for_update().get(pk=order_item.order_id)
    item = locked_order.items.select_for_update().select_related('product').get(pk=order_item.pk)
    if actor.id != locked_order.buyer_id and not actor.is_staff:
        raise ValidationError('Only the buyer or an administrator may cancel this line.')
    if locked_order.status not in {'PENDING', 'PAID'}:
        raise ValidationError(f'Lines cannot be cancelled from order status {locked_order.status}.')
    if quantity <= 0 or quantity > item.active_quantity:
        raise ValidationError('Cancellation quantity exceeds the active line quantity.')
    product = Product.objects.select_for_update().get(pk=item.product_id)
    refund_amount = item.price_snapshot * quantity
    if locked_order.status == 'PENDING':
        reservation = locked_order.reservations.select_for_update().get(product=item.product)
        reservation.quantity -= quantity
        product.reserved_stock -= quantity
        if reservation.quantity == 0:
            reservation.status = 'RELEASED'
        reservation.save(update_fields=['quantity', 'status', 'updated_at'])
        product.save(update_fields=['reserved_stock', 'updated_at'])
    else:
        product.stock += quantity
        product.save(update_fields=['stock', 'updated_at'])
        post_refund(order=locked_order, order_item=item, amount=refund_amount,
                    reference=f'line-refund:{item.id}:{item.cancelled_quantity + quantity}')
    item.cancelled_quantity += quantity
    item.refunded_amount += refund_amount if locked_order.status == 'PAID' else Decimal('0.00')
    item.cancellation_reason = reason
    item.save(update_fields=['cancelled_quantity', 'refunded_amount', 'cancellation_reason', 'updated_at'])
    if not locked_order.items.exclude(cancelled_quantity=models.F('quantity')).exists():
        locked_order.status = 'CANCELLED'
        locked_order.save(update_fields=['status', 'updated_at'])
    return item
