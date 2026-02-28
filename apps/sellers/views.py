from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Count, Sum, Q
from .models import Seller
from .serializers import SellerSerializer, SellerCreateSerializer, SellerUpdateSerializer
from apps.common.permissions import IsSeller


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
        if hasattr(request.user, 'seller'):
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
        if not hasattr(request.user, 'seller'):
            return Response(
                {'error': 'Seller profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        seller = request.user.seller
        serializer = SellerSerializer(seller, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'], parser_classes=[MultiPartParser, FormParser])
    def update_profile(self, request):
        """Update seller profile including images (authenticated seller only)."""
        if not hasattr(request.user, 'seller'):
            return Response(
                {'error': 'Seller profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        seller = request.user.seller
        serializer = SellerUpdateSerializer(seller, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(SellerSerializer(seller, context={'request': request}).data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsSeller])
    def orders(self, request):
        """
        Get orders containing current seller's products.
        
        GET /api/sellers/orders/
        
        Returns: Orders where seller has items (multi-seller support)
        Filters: Only orders with THIS seller's items
        """
        from apps.orders.models import Order
        from apps.orders.serializers import OrderSerializer
        
        if not hasattr(request.user, 'seller'):
            return Response(
                {'error': 'Seller profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get orders containing this seller's items
        orders = Order.objects.filter(
            items__seller=request.user.seller
        ).distinct().order_by('-created_at')
        
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsSeller])
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
        
        if not hasattr(request.user, 'seller'):
            return Response(
                {'error': 'Seller profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        seller = request.user.seller
        
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
