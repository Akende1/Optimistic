from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer
from apps.common.api import get_user_seller
from apps.common.permissions import IsBuyer


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
            return [IsBuyer()]
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
        auto = request.data.get('auto', False)
        
        # Verify buyer is confirming their own order
        if not auto and order.buyer != request.user:
            return Response({
                'error': 'Can only confirm your own orders.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            order.mark_delivered(confirmed_by_buyer=True)
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
