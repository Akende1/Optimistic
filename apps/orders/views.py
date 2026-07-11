from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError
from .models import Order, OrderFulfillment
from .serializers import OrderSerializer, OrderCreateSerializer, PaymentAttemptSerializer, OrderFulfillmentSerializer, OrderItemSerializer
from .services import create_payment_attempt, transition_fulfillment
from .services import record_verified_payment_event
from .services import simulate_payment_event
from .services import cancel_order_line
from .models import OrderItem
from django.conf import settings
from .models import PaymentAttempt
from .payments import get_adapter
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError as DRFValidationError
from apps.common.api import get_user_seller
from apps.common.permissions import IsBuyer, IsVerifiedAccount


class OrderViewSet(viewsets.ModelViewSet):
    """
    Order management viewset - transaction lifecycle.
    
    API Endpoints:
        GET /api/orders/           - List user's orders
        POST /api/orders/          - Create order (buyer only)
        GET /api/orders/{id}/      - Get order detail
        POST /api/orders/{id}/mark_paid/           - Mark as paid (payment callback)
        POST /api/orders/{id}/mark_ready/          - Mark ready for delivery (seller)
        POST /api/orders/{id}/mark_in_transit/     - Mark in transit (delivery partner)
        POST /api/orders/{id}/mark_delivered/      - Mark delivered (buyer/system)
        POST /api/orders/{id}/cancel/              - Cancel order (buyer/admin)
    
    Permission Logic:
        - List: Buyers see own orders, Sellers see orders for their products, Admins see all
        - Create: Buyers only
        - State transitions: Role-specific (see action decorators)
    
    Business Rules:
        - Orders follow strict state machine (PENDING → PAID → READY → IN_TRANSIT → DELIVERED)
        - Inventory deducted on PAID status
        - Notifications triggered on each status change
        - Can only cancel PENDING or PAID orders
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['status', 'order_type', 'buyer', 'created_at']
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']  # Default: newest first
    search_fields = ['id', 'buyer__username', 'po_number', 'company_name']

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    @action(detail=False, methods=['post'], url_path='delivery-quote')
    def delivery_quote(self, request):
        """Return the authoritative optional-leg delivery quote used by checkout."""
        from .delivery import quote_delivery
        try:
            quote = quote_delivery(
                zone_id=request.data.get('delivery_zone_id'),
                origin_pickup_required=bool(request.data.get('origin_pickup_required', False)),
                destination_delivery_required=bool(request.data.get('destination_delivery_required', False)),
            )
        except ValidationError as exc:
            raise DRFValidationError(exc.messages)
        return Response({key: str(value) if hasattr(value, 'as_tuple') else value for key, value in quote.items()})
    
    def get_queryset(self):
        """
        Dynamic queryset based on user role - STRICT SEPARATION.
        
        Access Control:
        - Buyers: Only their own orders
        - Sellers: ONLY orders containing THEIR products (via OrderItem)
        - Admins: All orders
        
        Multi-Seller Logic:
        - One order can have items from multiple sellers
        - Each seller sees only orders where they have items
        - Seller cannot see items from other sellers in same order
        """
        user = self.request.user
        
        # Admin sees all orders
        if user.is_staff:
            return Order.objects.all()
        
        # Buyers see their own orders only
        if user.role == 'BUYER':
            return Order.objects.filter(buyer=user)
        
        # Sellers see ONLY orders containing THEIR products
        if user.role == 'SELLER':
            seller = get_user_seller(user)
            if seller is None:
                return Order.objects.none()
            return Order.objects.filter(
                items__seller=seller
            ).distinct()  # Distinct to avoid duplicates from multiple items
        
        # Default: no orders (shouldn't reach here)
        return Order.objects.none()
    
    def get_permissions(self):
        """Role-based permissions for different actions."""
        if self.action == 'create':
            return [IsBuyer(), IsVerifiedAccount()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """
        Create order for current buyer.
        
        CRITICAL: Sellers CANNOT place orders - buyers only!
        """
        # Extra validation: ensure user is not a seller
        if get_user_seller(self.request.user) is not None:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Sellers cannot place orders. Please use a buyer account.')
        
        serializer.save(buyer=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_paid(self, request, pk=None):
        """
        Payment gateway callback: Mark order as paid.
        
        POST /api/orders/{id}/mark_paid/
        
        Transition: PENDING → PAID
        
        Business Rules:
        - Called by payment gateway webhook
        - Deducts inventory
        - Triggers notification to seller
        """
        order = self.get_object()
        if not request.user.is_staff:
            return Response({
                'error': 'Payment status can only be confirmed by the payment service or an administrator.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            order.mark_as_paid()
            return Response({
                'message': 'Order marked as paid.',
                'status': order.status,
                'order_id': order.id
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_ready(self, request, pk=None):
        """
        Seller action: Mark order as ready for delivery.
        
        POST /api/orders/{id}/mark_ready/
        
        Transition: PAID → READY_FOR_DELIVERY
        
        Business Rules:
        - Only seller can mark as ready
        - Seller can only mark orders containing THEIR products
        - Triggers notification to buyer
        """
        order = self.get_object()
        
        # Verify user is a seller
        seller = get_user_seller(request.user)
        if seller is None:
            return Response({
                'error': 'Only sellers can mark orders as ready'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verify this order contains seller's products
        if not order.items.filter(seller=seller).exists():
            return Response({
                'error': 'This order does not contain your products'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            order.mark_ready_for_delivery()
            return Response({
                'message': 'Order marked as ready for delivery.',
                'status': order.status
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_in_transit(self, request, pk=None):
        """
        Delivery partner action: Mark order as in transit.
        
        POST /api/orders/{id}/mark_in_transit/
        
        Transition: READY_FOR_DELIVERY → IN_TRANSIT
        
        Business Rules:
        - Only delivery partner can mark (when delivery partner auth implemented)
        - Triggers notification to buyer
        """
        order = self.get_object()
        if request.user.role != 'COURIER' and not request.user.is_staff:
            return Response({
                'error': 'Only a courier or administrator can mark an order in transit.'
            }, status=status.HTTP_403_FORBIDDEN)
        if order.delivery_partner_id and hasattr(order.delivery_partner, 'user_id'):
            if order.delivery_partner.user_id != request.user.id and not request.user.is_staff:
                return Response({'error': 'This order is assigned to another courier.'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            order.mark_in_transit()
            return Response({
                'message': 'Order marked as in transit.',
                'status': order.status
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_delivered(self, request, pk=None):
        """
        Buyer/System action: Confirm order delivered.
        
        POST /api/orders/{id}/mark_delivered/
        Request body: {"auto": false}
        
        Transition: IN_TRANSIT → DELIVERED
        
        Business Rules:
        - Buyer confirms manually, or system auto-confirms after X days
        - Enables buyer to leave review
        - Triggers notification to seller (payment release)
        """
        order = self.get_object()
        # Only trusted server-side jobs/admins may auto-confirm. Never trust a
        # client-provided flag to bypass ownership.
        auto = bool(request.data.get('auto', False)) and request.user.is_staff

        if not auto and order.buyer != request.user:
            return Response({
                'error': 'Can only confirm your own orders.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            order.mark_delivered(confirmed_by_buyer=not auto)
            return Response({
                'message': 'Order marked as delivered.',
                'status': order.status,
                'delivered_at': order.delivered_at,
                'can_review': True
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def confirm_delivery(self, request, pk=None):
        """
        Buyer action: Confirm receipt of delivery.
        
        POST /api/orders/{id}/confirm_delivery/
        
        Transition: IN_TRANSIT → DELIVERED
        
        Business Rules:
        - Only buyer can confirm their own order
        - Order must be IN_TRANSIT
        - Sets confirmed_by_buyer=True and delivered_at timestamp
        - Enables buyer to leave review
        - Triggers payment release to seller
        """
        order = self.get_object()
        
        # Verify buyer is confirming their own order
        if order.buyer != request.user:
            return Response({
                'error': 'Can only confirm your own orders.',
                'detail': f'This order belongs to {order.buyer.email}, but you are logged in as {request.user.email}.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if already confirmed
        if order.confirmed_by_buyer:
            return Response({
                'error': 'Order delivery already confirmed.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order.mark_delivered(confirmed_by_buyer=True)
            return Response({
                'message': 'Delivery confirmed! Thank you for your order.',
                'status': order.status,
                'delivered_at': order.delivered_at,
                'can_review': True
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """
        Buyer/Admin action: Cancel order.
        
        POST /api/orders/{id}/cancel/
        Request body: {"reason": "Changed my mind"}
        
        Transition: PENDING or PAID → CANCELLED
        
        Business Rules:
        - Buyer can cancel own orders (PENDING or PAID only)
        - Admin can cancel any order
        - Cannot cancel if IN_TRANSIT or DELIVERED
        - Restores inventory
        - Triggers refund (when payment gateway integrated)
        """
        order = self.get_object()
        reason = request.data.get('reason', '')
        
        # Verify buyer is cancelling their own order or user is admin
        if order.buyer != request.user and not request.user.is_staff:
            return Response({
                'error': 'Can only cancel your own orders.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            order.cancel(reason=reason)
            return Response({
                'message': 'Order cancelled.',
                'reason': reason,
                'status': order.status
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                'error': str(e),
                'current_status': order.status,
                'cancellable_statuses': ['PENDING', 'PAID']
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='payment-attempts')
    def payment_attempts(self, request, pk=None):
        """Create a replay-safe payment attempt for a mobile/web checkout."""
        order = self.get_object()
        if order.buyer_id != request.user.id:
            return Response({'error': 'Can only pay for your own order.'}, status=status.HTTP_403_FORBIDDEN)
        key = request.headers.get('Idempotency-Key')
        if not key:
            raise DRFValidationError({'idempotency_key': 'Idempotency-Key header is required.'})
        provider = request.data.get('provider', 'MOBILE_MONEY')
        try:
            attempt, created = create_payment_attempt(order=order, provider=provider, idempotency_key=key)
        except ValidationError as exc:
            raise DRFValidationError(exc.messages)
        return Response(PaymentAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='simulate-payment')
    def simulate_payment(self, request, pk=None):
        """Development-only payment completion using the production event service."""
        if not settings.PAYMENT_SIMULATION_ENABLED:
            return Response({'error': 'Payment simulation is disabled.'}, status=status.HTTP_404_NOT_FOUND)
        order = self.get_object()
        if order.buyer_id != request.user.id and not request.user.is_staff:
            return Response({'error': 'Can only simulate payment for your own order.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            attempt = PaymentAttempt.objects.get(pk=request.data.get('attempt_id'), order=order)
        except (PaymentAttempt.DoesNotExist, ValueError, TypeError):
            raise DRFValidationError({'attempt_id': 'A valid payment attempt for this order is required.'})
        event_id = request.data.get('event_id') or f'sim-{attempt.id}-{request.data.get("outcome", "CAPTURED").lower()}'
        try:
            _, applied = simulate_payment_event(
                attempt=attempt,
                outcome=request.data.get('outcome', 'CAPTURED'),
                external_event_id=event_id,
            )
        except ValidationError as exc:
            raise DRFValidationError(exc.messages)
        attempt.refresh_from_db()
        order.refresh_from_db()
        return Response({
            'applied': applied,
            'payment': PaymentAttemptSerializer(attempt).data,
            'order': OrderSerializer(order, context={'request': request}).data,
        })

    @action(detail=True, methods=['post'], url_path='cancel-line')
    def cancel_line(self, request, pk=None):
        order = self.get_object()
        try:
            item = order.items.get(pk=request.data.get('item_id'))
            quantity = int(request.data.get('quantity', 0))
            item = cancel_order_line(order_item=item, actor=request.user, quantity=quantity,
                                     reason=request.data.get('reason', ''))
        except OrderItem.DoesNotExist:
            raise DRFValidationError({'item_id': 'Order line was not found.'})
        except (ValueError, TypeError):
            raise DRFValidationError({'quantity': 'A positive integer is required.'})
        except ValidationError as exc:
            raise DRFValidationError(exc.messages)
        return Response(OrderItemSerializer(item, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='confirm-receipt')
    def confirm_receipt(self, request, pk=None):
        """Buyer confirms delivery and completes buyer protection immediately."""
        order = self.get_object()
        if order.buyer_id != request.user.id:
            return Response({'error': 'Can only confirm your own order.'}, status=status.HTTP_403_FORBIDDEN)
        if order.status == 'IN_TRANSIT':
            order.mark_delivered(confirmed_by_buyer=True)
        order.complete()
        return Response(OrderSerializer(order, context={'request': request}).data)


class OrderFulfillmentViewSet(viewsets.ReadOnlyModelViewSet):
    """Seller-scoped fulfillment commands used by web and mobile clients."""
    serializer_class = OrderFulfillmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return OrderFulfillment.objects.select_related('order', 'seller')
        seller = get_user_seller(self.request.user)
        return OrderFulfillment.objects.filter(seller=seller).select_related('order', 'seller') if seller else OrderFulfillment.objects.none()

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        fulfillment = self.get_object()
        seller = get_user_seller(request.user)
        if not seller:
            return Response({'error': 'Seller account required.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            fulfillment = transition_fulfillment(
                fulfillment=fulfillment, seller=seller,
                new_status=request.data.get('status', ''),
                carrier=request.data.get('carrier', ''),
                tracking_number=request.data.get('tracking_number', ''),
            )
        except ValidationError as exc:
            raise DRFValidationError(exc.messages)
        return Response(self.get_serializer(fulfillment).data)


from rest_framework.decorators import api_view, permission_classes

@api_view(['POST'])
@permission_classes([AllowAny])
def payment_webhook(request, provider):
    """Receive a signed provider callback; signature is checked over raw bytes."""
    try:
        normalized = get_adapter(provider).verify_and_normalize(request)
        event, applied = record_verified_payment_event(provider=provider.upper(), **normalized)
        return Response({'accepted': True, 'applied': applied, 'event_id': event.id})
    except (ValidationError, KeyError) as exc:
        return Response({'error': '; '.join(getattr(exc, 'messages', [str(exc)]))}, status=status.HTTP_400_BAD_REQUEST)
