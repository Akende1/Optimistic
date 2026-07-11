"""Transactional outbox creation and retry-safe local dispatcher."""
from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from .models import OutboxEvent, ProcessedEvent


def enqueue(*, topic, aggregate_type, aggregate_id, idempotency_key, payload):
    """Create an event in the caller's database transaction, once per key."""
    return OutboxEvent.objects.get_or_create(
        idempotency_key=idempotency_key,
        defaults={'topic': topic, 'aggregate_type': aggregate_type,
                  'aggregate_id': str(aggregate_id), 'payload': payload},
    )


HANDLERS = {}


def handler(topic):
    def register(function):
        HANDLERS[topic] = function
        return function
    return register


@handler('notification.order_status')
def create_order_notification(event):
    from apps.accounts.models import User
    from apps.notifications.models import Notification
    payload = event.payload
    user = User.objects.get(pk=payload['user_id'])
    Notification.objects.get_or_create(
        user=user, notification_type='ORDER', related_id=int(event.aggregate_id),
        title=payload['title'], defaults={'message': payload['message']},
    )


def dispatch_batch(limit=100, now=None):
    """Lock and process available events. Failed events use exponential backoff."""
    now = now or timezone.now()
    processed = 0
    with transaction.atomic():
        events = list(OutboxEvent.objects.select_for_update(skip_locked=True).filter(
            status__in=['PENDING', 'FAILED'], available_at__lte=now,
        )[:limit])
        for event in events:
            event.status, event.locked_at = 'PROCESSING', now
            event.save(update_fields=['status', 'locked_at'])
    for event in events:
        try:
            consumer = f'local:{event.topic}'
            with transaction.atomic():
                locked = OutboxEvent.objects.select_for_update().get(pk=event.pk)
                if ProcessedEvent.objects.filter(consumer=consumer, event=locked).exists():
                    locked.status, locked.published_at = 'PUBLISHED', timezone.now()
                    locked.save(update_fields=['status', 'published_at'])
                    continue
                callback = HANDLERS.get(locked.topic)
                if callback:
                    callback(locked)
                ProcessedEvent.objects.create(consumer=consumer, event=locked)
                locked.status, locked.published_at, locked.last_error = 'PUBLISHED', timezone.now(), ''
                locked.save(update_fields=['status', 'published_at', 'last_error'])
                processed += 1
        except Exception as exc:
            with transaction.atomic():
                failed = OutboxEvent.objects.select_for_update().get(pk=event.pk)
                failed.attempts += 1
                failed.status = 'FAILED'
                failed.last_error = str(exc)[:2000]
                failed.available_at = timezone.now() + timedelta(seconds=min(2 ** failed.attempts, 3600))
                failed.save(update_fields=['attempts', 'status', 'last_error', 'available_at'])
    return processed
