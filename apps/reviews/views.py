from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from .models import Review, Report
from .serializers import ReviewSerializer, ReportSerializer
from apps.common.permissions import IsBuyer
from apps.orders.models import OrderItem


class ReviewViewSet(viewsets.ModelViewSet):
    """
    Review viewset.
    
    GET /api/reviews/ - List all reviews (public)
    POST /api/reviews/ - Create review (authenticated buyers only)
    GET /api/reviews/{id}/ - Get review details
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Filter reviews by product or seller if specified."""
        queryset = Review.objects.all()
        product_id = self.request.query_params.get('product', None)
        seller_id = self.request.query_params.get('seller', None)

        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if seller_id:
            queryset = queryset.filter(seller_id=seller_id)

        return queryset

    def perform_create(self, serializer):
        """Create review with current user as reviewer."""
        if self.request.user.role != 'BUYER':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only buyers can submit product reviews.')

        serializer.save(reviewer=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsBuyer])
    def reviewables(self, request):
        """
        List delivered order items the buyer can still review.

        GET /api/reviews/reviewables/
        """
        delivered_items = OrderItem.objects.select_related('order', 'product', 'seller').filter(
            order__buyer=request.user,
            order__status='DELIVERED',
        ).order_by('-order__created_at', '-id')

        existing_reviews = {
            (review.order_id, review.product_id)
            for review in Review.objects.filter(reviewer=request.user).only('order_id', 'product_id')
        }

        results = []
        for item in delivered_items:
            key = (item.order_id, item.product_id)
            if key in existing_reviews:
                continue
            results.append({
                'order_id': item.order_id,
                'product_id': item.product_id,
                'product_name': item.product.name,
                'seller_id': item.seller_id,
                'seller_name': item.seller.store_name,
                'quantity': item.quantity,
                'price_snapshot': str(item.price_snapshot),
                'delivered_at': item.order.delivered_at,
                'order_created_at': item.order.created_at,
            })

        return Response({
            'count': len(results),
            'results': results,
        })


class ReportViewSet(viewsets.ModelViewSet):
    """
    Report viewset.
    
    GET /api/reports/ - List user's reports
    POST /api/reports/ - Create report
    GET /api/reports/{id}/ - Get report details
    """
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users see only their own reports."""
        return Report.objects.filter(reporter=self.request.user)

    def perform_create(self, serializer):
        """Create report with current user as reporter."""
        serializer.save(reporter=self.request.user)
