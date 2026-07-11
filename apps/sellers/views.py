from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Count, Sum, Q
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes, parser_classes
from .models import Seller
from .serializers import SellerSerializer, SellerCreateSerializer, SellerUpdateSerializer
from .serializers import SellerVerificationSerializer, SellerVerificationReviewSerializer
from apps.common.api import get_user_seller, model_field_available
from apps.common.permissions import IsSeller, IsVerifiedAccount


class SellerViewSet(viewsets.ModelViewSet):
    """
    Seller management viewset.
    
    GET /api/sellers/ - List all verified sellers (public)
    POST /api/sellers/ - Create seller profile (authenticated users)
    GET /api/sellers/{id}/ - Get seller details (public)
    GET /api/sellers/{id}/products/ - Get seller's products (public)
    """
    queryset = Seller.objects.filter(verified=True)
    serializer_class = SellerSerializer

    def get_queryset(self):
        queryset = Seller.objects.filter(verified=True)
        if not model_field_available(Seller, 'primary_location'):
            return queryset.defer('primary_location')
        return queryset
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SellerCreateSerializer
        return SellerSerializer
    
    def create(self, request, *args, **kwargs):
        """Create seller profile for current user."""
        existing_seller = get_user_seller(request.user)
        if existing_seller is not None:
            return Response(
                {'error': 'Seller profile already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.user.role == 'SELLER':
            return Response(
                {'error': 'User is already a seller'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        seller = serializer.save()
        
        return Response(
            SellerSerializer(seller).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get all products for a seller."""
        seller = self.get_object()
        from apps.products.models import Product
        from apps.products.serializers import ProductSerializer
        
        products = Product.objects.filter(seller=seller, status='ACTIVE')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's seller profile."""
        seller = get_user_seller(request.user)
        if seller is None:
            return Response(
                {'error': 'Seller profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SellerSerializer(seller, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'post'], permission_classes=[IsAuthenticated])
    def payout_requests(self, request):
        """List or create manual MVP withdrawal requests for the current seller."""
        from apps.finances.models import SellerPayoutRequest
        seller = get_user_seller(request.user)
        if seller is None or not seller.verified:
            return Response({'error': 'Verified seller account required.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'GET':
            rows = seller.payout_requests.order_by('-requested_at').values(
                'id', 'amount', 'provider', 'status', 'requested_at', 'processed_at', 'provider_reference'
            )
            return Response(list(rows))
        payout = SellerPayoutRequest(
            seller=seller, amount=request.data.get('amount'), provider=seller.payout_provider,
            account_name=seller.payout_account_name, account_number=seller.payout_account_number,
        )
        try:
            payout.full_clean()
            payout.save()
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'id': payout.id, 'amount': payout.amount, 'provider': payout.provider,
                         'status': payout.status}, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['patch'], parser_classes=[MultiPartParser, FormParser])
    def update_profile(self, request):
        """Update seller profile including images (authenticated seller only)."""
        seller = get_user_seller(request.user)
        if seller is None:
            return Response(
                {'error': 'Seller profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SellerUpdateSerializer(seller, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(SellerSerializer(seller, context={'request': request}).data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsSeller, IsVerifiedAccount])
    def orders(self, request):
        """
        Get orders containing current seller's products.
        
        GET /api/sellers/orders/
        
        Returns: Orders where seller has items (multi-seller support)
        Filters: Only orders with THIS seller's items
        """
        from apps.orders.models import Order
        from apps.orders.serializers import OrderSerializer
        
        seller = get_user_seller(request.user)
        if seller is None:
            return Response(
                {'error': 'Seller profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get orders containing this seller's items
        orders = Order.objects.filter(
            items__seller=seller
        ).distinct().order_by('-created_at')
        
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsSeller, IsVerifiedAccount])
    def analytics(self, request):
        """
        Get seller-specific analytics and metrics.
        
        GET /api/sellers/analytics/
        
        Returns:
        - Total products
        - Active products
        - Total orders
        - Total revenue
        - Products by status
        """
        from apps.products.models import Product
        from apps.orders.models import Order, OrderItem
        
        seller = get_user_seller(request.user)
        if seller is None:
            return Response(
                {'error': 'Seller profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Product metrics - ONLY this seller's products
        products = Product.objects.filter(seller=seller)
        products_by_status = products.values('status').annotate(count=Count('id'))
        
        # Order metrics - ONLY orders with this seller's items
        seller_orders = Order.objects.filter(items__seller=seller).distinct()
        
        # Revenue - ONLY from this seller's items
        seller_items = OrderItem.objects.filter(seller=seller)
        total_revenue = seller_items.aggregate(
            total=Sum('price_snapshot')
        )['total'] or 0
        
        # Orders by status - ONLY orders with this seller's items
        orders_by_status = seller_orders.values('status').annotate(count=Count('id'))
        
        analytics = {
            'products': {
                'total': products.count(),
                'active': products.filter(status='ACTIVE').count(),
                'draft': products.filter(status='DRAFT').count(),
                'pending': products.filter(status='PENDING_APPROVAL').count(),
                'suspended': products.filter(status='SUSPENDED').count(),
                'by_status': list(products_by_status)
            },
            'orders': {
                'total': seller_orders.count(),
                'pending': seller_orders.filter(status='PENDING').count(),
                'paid': seller_orders.filter(status='PAID').count(),
                'in_transit': seller_orders.filter(status='IN_TRANSIT').count(),
                'delivered': seller_orders.filter(status='DELIVERED').count(),
                'by_status': list(orders_by_status)
            },
            'revenue': {
                'total': float(total_revenue),
                'items_sold': seller_items.count()
            }
        }
        
        return Response(analytics)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSeller])
def seller_verification_status(request):
    """Get the current seller KYC status and documents."""
    seller = get_user_seller(request.user)
    if seller is None:
        return Response({'error': 'Seller profile not found'}, status=status.HTTP_404_NOT_FOUND)

    verification = getattr(seller, 'kyc_documents', None)
    verification_data = SellerVerificationSerializer(verification, context={'request': request}).data if verification else None

    return Response({
        'seller': SellerSerializer(seller, context={'request': request}).data,
        'can_publish_products': seller.can_publish_products(),
        'verification': verification_data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSeller, IsVerifiedAccount])
@parser_classes([MultiPartParser, FormParser])
@transaction.atomic
def submit_seller_verification(request):
    """Create or update the seller KYC packet and submit it for review."""
    seller = get_user_seller(request.user)
    if seller is None:
        return Response({'error': 'Seller profile not found'}, status=status.HTTP_404_NOT_FOUND)

    if seller.verified and seller.verification_status == 'VERIFIED':
        return Response({'error': 'Seller is already verified.'}, status=status.HTTP_400_BAD_REQUEST)
    from apps.common.legal import has_current_acceptance, record_acceptance
    if str(request.data.get('accepts_seller_terms', '')).lower() in {'true', '1', 'yes'}:
        record_acceptance(user=request.user, document='SELLER_TERMS', request=request)
    if not has_current_acceptance(request.user, 'SELLER_TERMS'):
        return Response({'error': 'Accept the current Seller Marketplace Terms before KYC submission.'}, status=status.HTTP_400_BAD_REQUEST)

    verification = getattr(seller, 'kyc_documents', None)
    serializer = SellerVerificationSerializer(
        instance=verification,
        data=request.data,
        context={'request': request, 'seller': seller},
    )
    serializer.is_valid(raise_exception=True)
    verification = serializer.save()

    return Response(
        {
            'message': 'KYC documents submitted for review.',
            'seller': SellerSerializer(seller, context={'request': request}).data,
            'verification': SellerVerificationSerializer(verification, context={'request': request}).data,
        },
        status=status.HTTP_201_CREATED if verification.status == 'PENDING' else status.HTTP_200_OK,
    )
