from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from apps.products.models import Product
from apps.orders.models import Order
from apps.notifications.models import Notification
from apps.common.permissions import IsSeller


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSeller])
def seller_dashboard(request):
    """
    Seller dashboard overview - business metrics.
    
    Endpoint: GET /api/sellers/dashboard/
    
    Returns:
    {
        "total_products": 15,
        "active_products": 12,
        "draft_products": 2,
        "total_orders": 45,  (stub - needs OrderItem)
        "pending_orders": 3,  (stub)
        "recent_notifications": [...]
    }
    
    Purpose: Dashboard homepage showing business health
    
    Access Control:
    - Must be authenticated
    - Must have SELLER role
    - Only sees their own data
    
    Performance:
    - Uses .count() for efficiency
    - No N+1 queries
    - Fast with thousands of records
    
    Future Enhancements:
    - Revenue totals (when payment integrated)
    - Sales charts (daily/weekly/monthly)
    - Product performance (views, conversion)
    - Customer insights (repeat buyers)
    - Inventory alerts (low stock)
    """
    seller = request.user.seller

    # Product statistics
    total_products = Product.objects.filter(seller=seller).count()
    active_products = Product.objects.filter(seller=seller, status='ACTIVE').count()
    draft_products = Product.objects.filter(seller=seller, status='DRAFT').count()

    # Order statistics (stub - needs order-product relationship)
    # For now, return placeholder
    total_orders = 0
    pending_orders = 0

    # Recent notifications
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    )[:5]

    return Response({
        'store_name': seller.store_name,
        'verified': seller.verified,
        'stats': {
            'total_products': total_products,
            'active_products': active_products,
            'draft_products': draft_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
        },
        'unread_notifications': notifications.count(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSeller])
def my_products(request):
    """
    Get seller's products with stats.
    GET /api/sellers/my-products/
    """
    seller = request.user.seller
    products = Product.objects.filter(seller=seller).order_by('-created_at')

    from apps.products.serializers import ProductSerializer
    serializer = ProductSerializer(products, many=True)
    
    return Response({
        'count': products.count(),
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSeller])
def my_orders(request):
    """
    Get orders for seller's products (stub).
    GET /api/sellers/my-orders/
    """
    # This needs OrderItem model to link orders to products
    # For now, return empty list
    return Response({
        'count': 0,
        'results': []
    })
