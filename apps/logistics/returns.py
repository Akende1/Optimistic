"""Reverse-logistics domain service. No payment or ledger mutation belongs here."""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import ReturnLine, ReturnRequest
from apps.common.outbox import enqueue

TRANSITIONS = {'REQUESTED': {'APPROVED', 'REJECTED'}, 'APPROVED': {'COURIER_ASSIGNED'}, 'COURIER_ASSIGNED': {'PICKED_UP'}, 'PICKED_UP': {'IN_TRANSIT'}, 'IN_TRANSIT': {'SELLER_RECEIVED'}, 'SELLER_RECEIVED': {'CONDITION_VERIFIED'}, 'CONDITION_VERIFIED': {'REFUND_AUTHORIZED', 'CLOSED'}, 'REFUND_AUTHORIZED': {'CLOSED'}}


@transaction.atomic
def create_return(*, order, buyer, lines, reason):
    if order.buyer_id != buyer.id or order.status not in {'DELIVERED', 'COMPLETED', 'DISPUTED'}:
        raise ValidationError('Return requires the delivered order owner.')
    result = ReturnRequest.objects.create(order=order, requested_by=buyer, reason=reason)
    for item, quantity in lines:
        if quantity <= 0 or quantity > item.active_quantity:
            raise ValidationError('Invalid return quantity.')
        ReturnLine.objects.create(return_request=result, order_item=item, quantity=quantity)
    return result


@transaction.atomic
def transition_return(*, return_request, actor, new_status, inspection=None):
    result = ReturnRequest.objects.select_for_update().get(pk=return_request.pk)
    if new_status not in TRANSITIONS.get(result.status, set()):
        raise ValidationError(f'Invalid return transition {result.status} -> {new_status}.')
    if new_status in {'APPROVED', 'REJECTED', 'CONDITION_VERIFIED', 'REFUND_AUTHORIZED'} and not actor.is_staff:
        raise ValidationError('Administrative authorization required.')
    if new_status == 'CONDITION_VERIFIED':
        if not inspection:
            raise ValidationError('Inspection results are required.')
        for line in result.lines.all():
            data = inspection.get(str(line.id), {})
            line.condition = data.get('condition', '')
            line.inspection_notes = data.get('notes', '')
            line.full_clean()
            line.save(update_fields=['condition', 'inspection_notes'])
    result.status = new_status
    if new_status == 'APPROVED':
        result.return_by = timezone.now() + timezone.timedelta(days=7)
    result.save(update_fields=['status', 'return_by', 'updated_at'])
    if new_status == 'REFUND_AUTHORIZED':
        enqueue(topic='finance.return_refund_authorized', aggregate_type='ReturnRequest', aggregate_id=result.id,
                idempotency_key=f'return-refund-authorized:{result.id}', payload={'return_id': result.id})
    return result
