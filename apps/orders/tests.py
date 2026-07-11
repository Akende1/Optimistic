from types import SimpleNamespace
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.finances.models import OrderFinancialSnapshot
from apps.finances.models import LedgerTransaction
from apps.finances.services import assert_transaction_balanced
from apps.common.models import OutboxEvent, ProcessedEvent
from apps.common.outbox import dispatch_batch
from apps.notifications.models import Notification
from apps.logistics.models import ZambianLocation
from .delivery import quote_delivery
from apps.products.models import Category, Product
from apps.sellers.models import Seller
from .models import Order
from .serializers import OrderCreateSerializer
from .models import InventoryReservation, PaymentAttempt
from .services import create_payment_attempt, expire_inventory_reservations, record_verified_payment_event
from .services import cancel_order_line
from django.utils import timezone
from rest_framework.test import APIClient


class OrderWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.buyer = user_model.objects.create_user(username='buyer', role='BUYER')
        seller_user = user_model.objects.create_user(username='seller', role='SELLER')
        self.seller = Seller.objects.create(
            user=seller_user, store_name='Test Store', phone='0970000000', verified=True
        )
        category = Category.objects.create(name='Test', slug='test')
        self.product = Product.objects.create(
            seller=self.seller,
            category=category,
            name='Widget',
            description='Test widget',
            price='125.50',
            stock=10,
            status='ACTIVE',
        )
        self.zone = ZambianLocation.objects.create(name='Lusaka CBD', location_type='ZONE', delivery_base_cost='50.00')

    def create_order(self, quantity=2):
        serializer = OrderCreateSerializer(
            data={
                'shipping_address': '1 Test Road, Lusaka',
                'delivery_zone_id': self.zone.id,
                'total_amount': '0.01',  # Must be ignored.
                'items': [{'product': self.product.id, 'quantity': quantity}],
            },
            context={'request': SimpleNamespace(user=self.buyer)},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        return serializer.save()

    def test_checkout_snapshots_price_and_calculates_total_server_side(self):
        order = self.create_order()
        self.assertEqual(order.product_subtotal, Decimal('251.00'))
        self.assertEqual(order.delivery_fee, Decimal('50.00'))
        self.assertEqual(order.total_amount, Decimal('301.00'))
        self.assertEqual(order.items.get().price_snapshot, Decimal('125.50'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)
        self.assertEqual(self.product.reserved_stock, 2)
        self.assertEqual(InventoryReservation.objects.get(order=order).status, 'ACTIVE')

    def test_payment_deducts_stock_once_and_creates_financial_snapshot(self):
        order = self.create_order(3)
        self.assertTrue(order.mark_as_paid())
        self.assertFalse(order.mark_as_paid())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)
        self.assertTrue(OrderFinancialSnapshot.objects.filter(order=order).exists())
        self.assertEqual(InventoryReservation.objects.get(order=order).status, 'CONSUMED')

    def test_paid_cancellation_restores_stock_once(self):
        order = self.create_order(4)
        order.mark_as_paid()
        order.cancel(reason='Changed mind')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)
        self.assertEqual(order.status, 'CANCELLED')

    def test_delivery_sets_real_fields(self):
        order = self.create_order()
        order.mark_as_paid()
        order.mark_ready_for_delivery()
        order.mark_in_transit()
        order.mark_delivered(confirmed_by_buyer=True)
        self.assertIsNotNone(order.delivered_at)
        self.assertTrue(order.confirmed_by_buyer)
        self.assertIsNotNone(order.protection_expires_at)

    def test_payment_attempt_and_event_are_idempotent(self):
        order = self.create_order()
        attempt, created = create_payment_attempt(order=order, provider='TEST', idempotency_key='pay-1')
        replay, replay_created = create_payment_attempt(order=order, provider='TEST', idempotency_key='pay-1')
        self.assertTrue(created)
        self.assertFalse(replay_created)
        self.assertEqual(attempt.id, replay.id)
        payload = {'amount': '301.00', 'currency': 'ZMW', 'payment_reference': 'provider-1'}
        _, applied = record_verified_payment_event(
            attempt_id=attempt.id, provider='TEST', external_event_id='event-1',
            event_type='payment.captured', payload=payload,
        )
        _, replay_applied = record_verified_payment_event(
            attempt_id=attempt.id, provider='TEST', external_event_id='event-1',
            event_type='payment.captured', payload=payload,
        )
        self.assertTrue(applied)
        self.assertFalse(replay_applied)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'CAPTURED')
        ledger_tx = LedgerTransaction.objects.get(reference=f'payment-capture:{attempt.id}')
        self.assertTrue(assert_transaction_balanced(ledger_tx))
        event = OutboxEvent.objects.get(idempotency_key=f'order-paid-notification:{order.id}')
        self.assertEqual(event.status, 'PENDING')
        self.assertEqual(dispatch_batch(), 1)
        event.refresh_from_db()
        self.assertEqual(event.status, 'PUBLISHED')
        self.assertTrue(ProcessedEvent.objects.filter(event=event).exists())
        self.assertTrue(Notification.objects.filter(user=self.buyer, related_id=order.id).exists())
        self.assertEqual(dispatch_batch(), 0)

    def test_paid_line_partial_cancellation_restores_stock_and_posts_refund(self):
        order = self.create_order(4)
        attempt, _ = create_payment_attempt(order=order, provider='TEST', idempotency_key='refund-pay')
        record_verified_payment_event(
            attempt_id=attempt.id, provider='TEST', external_event_id='refund-capture',
            event_type='payment.captured',
            payload={'amount': '552.00', 'currency': 'ZMW', 'payment_reference': 'refund-provider'},
        )
        item = cancel_order_line(order_item=order.items.get(), actor=self.buyer, quantity=1, reason='One damaged')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)
        self.assertEqual(item.cancelled_quantity, 1)
        self.assertEqual(item.refunded_amount, Decimal('125.50'))
        refund = LedgerTransaction.objects.get(reference=f'line-refund:{item.id}:1')
        self.assertTrue(assert_transaction_balanced(refund))

    def test_expired_reservation_releases_stock(self):
        order = self.create_order(2)
        reservation = order.reservations.get()
        reservation.expires_at = timezone.now() - timezone.timedelta(seconds=1)
        reservation.save(update_fields=['expires_at'])
        self.assertEqual(expire_inventory_reservations(), 1)
        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.product.reserved_stock, 0)
        self.assertEqual(order.status, 'EXPIRED')

    def test_optional_delivery_legs_are_explicit_and_buyer_paid(self):
        quote = quote_delivery(zone_id=self.zone.id, origin_pickup_required=True, destination_delivery_required=True)
        self.assertEqual(quote['origin_pickup_fee'], Decimal('40.00'))
        self.assertEqual(quote['inter_district_fee'], Decimal('50.00'))
        self.assertEqual(quote['destination_delivery_fee'], Decimal('40.00'))
        self.assertEqual(quote['delivery_fee'], Decimal('130.00'))
        self.assertEqual(quote['delivery_service'], 'DOOR_TO_DOOR')

    def test_mobile_payment_simulation_and_replay(self):
        order = self.create_order()
        attempt, _ = create_payment_attempt(order=order, provider='TEST', idempotency_key='mobile-pay')
        client = APIClient()
        client.force_authenticate(self.buyer)
        url = f'/api/v1/orders/{order.id}/simulate-payment/'
        body = {'attempt_id': str(attempt.id), 'outcome': 'CAPTURED', 'event_id': 'mobile-event-1'}
        response = client.post(url, body, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data['applied'])
        replay = client.post(url, body, format='json')
        self.assertEqual(replay.status_code, 200, replay.data)
        self.assertFalse(replay.data['applied'])

    def test_other_buyer_cannot_access_or_simulate_order(self):
        order = self.create_order()
        other = get_user_model().objects.create_user(username='other', role='BUYER')
        client = APIClient()
        client.force_authenticate(other)
        response = client.post(f'/api/v1/orders/{order.id}/simulate-payment/', {}, format='json')
        # Role-scoped queryset deliberately hides the order instead of leaking it.
        self.assertEqual(response.status_code, 404)

    def test_unverified_buyer_cannot_checkout(self):
        client = APIClient(); client.force_authenticate(self.buyer)
        response = client.post('/api/v1/orders/', {}, format='json')
        self.assertEqual(response.status_code, 403)
