from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from .models import Delivery, DeliveryPartner, ZambianLocation
from .serializers import (
    DeliverySerializer, 
    DeliveryPartnerSerializer,
    DeliveryPartnerRegistrationSerializer,
    ZambianLocationSerializer
)


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
        if user.role == 'SELLER':
            # Sellers see deliveries for their orders
            return Delivery.objects.filter(order__seller=user.seller)
        else:
            # Buyers see their own order deliveries
            return Delivery.objects.filter(order__buyer=user)


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
    
    @action(detail=False, methods=['get'])
    def cities(self, request):
        """Get cities, optionally filtered by province."""
        queryset = ZambianLocation.objects.filter(
            location_type='CITY',
            is_active=True
        )
        
        province_id = request.query_params.get('province', None)
        if province_id:
            queryset = queryset.filter(parent_id=province_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
