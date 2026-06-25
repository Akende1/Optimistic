from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, F, Sum, DecimalField, ExpressionWrapper
from apps.products.models import Product
from apps.orders.models import Order, OrderItem
from apps.notifications.models import Notification
from apps.common.api import get_user_seller
from apps.common.permissions import IsSeller, IsVerifiedAccount


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSeller, IsVerifiedAccount])
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
    seller = get_user_seller(request.user)
    if seller is None:
        return Response({'error': 'Seller profile not found'}, status=404)

    # Product statistics
    products = Product.objects.filter(seller=seller).order_by('-created_at')
    total_products = products.count()
    active_products = products.filter(status='ACTIVE').count()
    draft_products = products.filter(status='DRAFT').count()
    pending_products = products.filter(status='PENDING_APPROVAL').count()
    suspended_products = products.filter(status='SUSPENDED').count()

    # Order statistics from the seller's line items
    seller_orders = Order.objects.filter(items__seller=seller).distinct().order_by('-created_at')
    total_orders = seller_orders.count()
    pending_orders = seller_orders.filter(status='PENDING').count()

    seller_items = OrderItem.objects.filter(seller=seller)
    revenue_expression = ExpressionWrapper(
        F('price_snapshot') * F('quantity'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    total_revenue = seller_items.aggregate(total=Sum(revenue_expression))['total'] or 0

    recent_products = [
        {
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
            'stock': product.stock,
            'status': product.status,
            'created_at': product.created_at,
        }
        for product in products[:5]
    ]

    recent_orders = [
        {
            'id': order.id,
            'status': order.status,
            'status_display': order.get_status_display(),
            'total_amount': str(order.total_amount),
            'created_at': order.created_at,
            'item_count': order.items.filter(seller=seller).count(),
        }
        for order in seller_orders[:5]
    ]

    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:5]

    return Response({
        'store_name': seller.store_name,
        'verified': seller.verified,
        'verification_status': seller.verification_status,
        'completion_percentage': seller.get_completion_percentage(),
        'profile_image_url': request.build_absolute_uri(seller.profile_image.url) if seller.profile_image else None,
        'banner_image_url': request.build_absolute_uri(seller.banner_image.url) if seller.banner_image else None,
        'stats': {
            'total_products': total_products,
            'active_products': active_products,
            'draft_products': draft_products,
            'pending_products': pending_products,
            'suspended_products': suspended_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_revenue': str(total_revenue),
        },
        'recent_products': recent_products,
        'recent_orders': recent_orders,
        'notifications': [
            {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'created_at': notification.created_at,
            }
            for notification in notifications
        ],
        'unread_notifications': unread_notifications,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSeller, IsVerifiedAccount])
def my_products(request):
    """
    Get seller's products with stats.
    GET /api/sellers/my-products/
    """
    seller = get_user_seller(request.user)
    if seller is None:
        return Response({'error': 'Seller profile not found'}, status=404)
    products = Product.objects.filter(seller=seller).order_by('-created_at')

    from apps.products.serializers import ProductSerializer
    serializer = ProductSerializer(products, many=True)
    
    return Response({
        'count': products.count(),
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSeller, IsVerifiedAccount])
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
