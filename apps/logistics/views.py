from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from .models import Delivery, DeliveryPartner, ZambianLocation, DeliveryEvent, ReturnRequest
from django.db import transaction
from django.utils import timezone
from .serializers import (
    DeliverySerializer, 
    DeliveryPartnerSerializer,
    DeliveryPartnerRegistrationSerializer,
    ZambianLocationSerializer, ReturnRequestSerializer
)
from .returns import create_return, transition_return
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from apps.common.api import get_user_seller


class DeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Delivery tracking viewset.
    Users can view deliveries for their orders.
    """
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users see deliveries for their orders only."""
        user = self.request.user
        if user.is_staff:
            return Delivery.objects.all()
        if user.role == 'COURIER':
            return Delivery.objects.filter(partner__user=user)
        if user.role == 'SELLER':
            # Sellers see deliveries for their orders
            seller = get_user_seller(user)
            if seller is None:
                return Delivery.objects.none()
            return Delivery.objects.filter(order__items__seller=seller).distinct()
        else:
            # Buyers see their own order deliveries
            return Delivery.objects.filter(order__buyer=user)

    @action(detail=True, methods=['post'], url_path='events')
    def add_event(self, request, pk=None):
        delivery = self.get_object()
        if request.user.role != 'COURIER' and not request.user.is_staff:
            return Response({'error': 'Courier or administrator required.'}, status=status.HTTP_403_FORBIDDEN)
        if not request.user.is_staff and delivery.partner_id and delivery.partner.user_id != request.user.id:
            return Response({'error': 'Delivery is assigned to another courier.'}, status=status.HTTP_403_FORBIDDEN)
        new_status = request.data.get('status')
        if new_status not in dict(Delivery.STATUS_CHOICES):
            return Response({'status': 'Invalid delivery status.'}, status=status.HTTP_400_BAD_REQUEST)
        transitions = {
            'REQUESTED': {'ASSIGNED', 'CANCELLED'}, 'ASSIGNED': {'PICKED_UP', 'EXCEPTION', 'CANCELLED'},
            'PICKED_UP': {'IN_TRANSIT', 'EXCEPTION'}, 'IN_TRANSIT': {'OUT_FOR_DELIVERY', 'EXCEPTION'},
            'OUT_FOR_DELIVERY': {'DELIVERED', 'FAILED', 'EXCEPTION'},
            'FAILED': {'OUT_FOR_DELIVERY', 'RETURNED'}, 'EXCEPTION': {'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'RETURNED', 'LOST'},
        }
        if new_status not in transitions.get(delivery.status, set()):
            return Response({'error': f'Invalid delivery transition {delivery.status} -> {new_status}.'}, status=status.HTTP_409_CONFLICT)
        with transaction.atomic():
            event, created = DeliveryEvent.objects.get_or_create(
                source=request.data.get('source', 'COURIER'),
                external_event_id=request.data.get('external_event_id'),
                defaults={'delivery': delivery, 'status': new_status, 'location': request.data.get('location', ''),
                          'description': request.data.get('description', ''), 'occurred_at': request.data.get('occurred_at', timezone.now())},
            )
            if created:
                delivery.status = new_status
                if new_status == 'PICKED_UP':
                    delivery.picked_up_at = event.occurred_at
                if new_status == 'DELIVERED':
                    delivery.delivered_at = event.occurred_at
                    if delivery.order.status == 'IN_TRANSIT':
                        delivery.order.mark_delivered(confirmed_by_buyer=False)
                delivery.save(update_fields=['status', 'picked_up_at', 'delivered_at'])
                from apps.common.outbox import enqueue
                enqueue(
                    topic='notification.order_status', aggregate_type='Delivery', aggregate_id=delivery.id,
                    idempotency_key=f'delivery-event-notification:{event.id}',
                    payload={'user_id': delivery.order.buyer_id, 'title': f'Delivery update: {new_status}',
                             'message': event.description or f'Your delivery is now {new_status}.'},
                )
        return Response({'accepted': True, 'applied': created})


class DeliveryPartnerViewSet(viewsets.ModelViewSet):
    """
    Delivery partner management viewset.
    
    API Endpoints:
        GET /api/delivery-partners/              - List active partners
        POST /api/delivery-partners/register/    - Register new courier (public)
        GET /api/delivery-partners/{id}/         - Get partner details
        PUT /api/delivery-partners/{id}/         - Update partner profile
        POST /api/delivery-partners/{id}/verify/ - Verify partner (admin only)
        GET /api/delivery-partners/pending/      - List unverified partners (admin)
    """
    serializer_class = DeliveryPartnerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter based on user role and verification status."""
        user = self.request.user
        
        if user.is_staff:
            # Admins see all partners
            return DeliveryPartner.objects.all()
        
        # Regular users see only verified, active partners
        return DeliveryPartner.objects.filter(verified=True, is_active=True)
    
    def get_permissions(self):
        """Allow public registration, require auth for other actions."""
        if self.action == 'register':
            return [AllowAny()]
        return super().get_permissions()
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Public endpoint for courier onboarding.
        
        POST /api/delivery-partners/register/
        {
            "username": "courier_name",
            "password": "securepass",
            "name": "John Banda",
            "phone": "+260977123456",
            "email": "john@example.com",
            "partner_type": "RIDER",
            "service_area": "Lusaka CBD, Kabulonga",
            "vehicle_type": "Motorcycle",
            "id_number": "123456/78/9"
        }
        """
        serializer = DeliveryPartnerRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            partner = serializer.save()
            return Response({
                'message': 'Registration successful! Your account is pending admin verification.',
                'partner_id': partner.id,
                'username': partner.user.username,
                'verified': partner.verified
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def verify(self, request, pk=None):
        """
        Admin action: Verify delivery partner.
        
        POST /api/delivery-partners/{id}/verify/
        """
        partner = self.get_object()
        partner.verified = True
        partner.save()
        
        return Response({
            'message': f'{partner.name} has been verified.',
            'verified': True
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending(self, request):
        """
        Admin endpoint: List all unverified partners.
        
        GET /api/delivery-partners/pending/
        """
        pending_partners = DeliveryPartner.objects.filter(verified=False)
        serializer = self.get_serializer(pending_partners, many=True)
        return Response(serializer.data)


class ZambianLocationViewSet(viewsets.ModelViewSet):
    """
    Zambian locations API for provinces, cities, and zones.
    
    API Endpoints:
        GET /api/locations/                  - List all locations
        GET /api/locations/?type=PROVINCE    - Filter by type
        GET /api/locations/?parent=1         - Get children of location
        GET /api/locations/provinces/        - Get all provinces
        GET /api/locations/cities/?province=1 - Get cities in province
    """
    queryset = ZambianLocation.objects.filter(is_active=True)
    serializer_class = ZambianLocationSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by type (PROVINCE, CITY, ZONE)
        location_type = self.request.query_params.get('type', None)
        if location_type:
            queryset = queryset.filter(location_type=location_type)
        
        # Filter by parent (get children)
        parent_id = self.request.query_params.get('parent', None)
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def provinces(self, request):
        """Get all Zambian provinces."""
        provinces = ZambianLocation.objects.filter(
            location_type='PROVINCE',
            is_active=True
        )
        serializer = self.get_serializer(provinces, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        try:
            partner = DeliveryPartner.objects.get(user=request.user)
        except DeliveryPartner.DoesNotExist:
            return Response({'error': 'Courier profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        if request.method == 'PATCH':
            serializer = self.get_serializer(partner, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(self.get_serializer(partner).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def earnings(self, request):
        try:
            partner = DeliveryPartner.objects.get(user=request.user)
        except DeliveryPartner.DoesNotExist:
            return Response({'error': 'Courier profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        wallet = getattr(partner, 'wallet', None)
        rows = partner.earnings.select_related('delivery').values(
            'id', 'delivery_id', 'amount', 'status', 'created_at', 'cleared_at', 'paid_at'
        )
        return Response({
            'wallet': {
                'available': str(wallet.available_balance if wallet else 0),
                'pending': str(wallet.pending_balance if wallet else 0),
                'lifetime': str(wallet.lifetime_earnings if wallet else 0),
            },
            'results': list(rows),
        })

    @action(detail=False, methods=['get'])
    def cities(self, request):
        """Get cities, optionally filtered by province."""
        queryset = ZambianLocation.objects.filter(location_type='CITY', is_active=True)
        province_id = request.query_params.get('province')
        if province_id:
            queryset = queryset.filter(parent_id=province_id)
        return Response(self.get_serializer(queryset, many=True).data)


class ReturnRequestViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                           mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ReturnRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ReturnRequest.objects.all().prefetch_related('lines')
        seller = get_user_seller(user)
        if seller:
            return ReturnRequest.objects.filter(order__items__seller=seller).distinct().prefetch_related('lines')
        return ReturnRequest.objects.filter(requested_by=user).prefetch_related('lines')

    def create(self, request, *args, **kwargs):
        from apps.orders.models import Order, OrderItem
        try:
            order = Order.objects.get(pk=request.data.get('order'), buyer=request.user)
            lines = [(OrderItem.objects.get(pk=line['order_item'], order=order), int(line['quantity']))
                     for line in request.data.get('lines', [])]
            result = create_return(order=order, buyer=request.user, lines=lines, reason=request.data.get('reason', ''))
        except (Order.DoesNotExist, OrderItem.DoesNotExist, KeyError, TypeError, ValueError, ValidationError) as exc:
            raise DRFValidationError(getattr(exc, 'messages', [str(exc)]))
        return Response(self.get_serializer(result).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        try:
            result = transition_return(return_request=self.get_object(), actor=request.user,
                                       new_status=request.data.get('status', ''), inspection=request.data.get('inspection'))
        except ValidationError as exc:
            raise DRFValidationError(exc.messages)
        return Response(self.get_serializer(result).data)
