from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import Review, Report
from .serializers import ReviewSerializer, ReportSerializer


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
        serializer.save(reviewer=self.request.user)


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
