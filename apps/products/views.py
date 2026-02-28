from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from .models import Category, Product, ProductImage
from .serializers import (
    CategorySerializer, 
    ProductSerializer, 
    ProductCreateSerializer,
    ProductImageUploadSerializer
)
from apps.common.permissions import IsVerifiedSeller, IsOwnerOrReadOnly


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Category viewset (read-only for all).
    
    GET /api/categories/ - List all active categories
    GET /api/categories/{id}/ - Get category details
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = []


class ProductViewSet(viewsets.ModelViewSet):
    """
    Product management viewset - the marketplace catalog.
    
    API Endpoints:
        GET /api/products/          - List all active products (public)
        POST /api/products/         - Create product (authenticated sellers only)
        GET /api/products/{id}/     - Get product detail (public if active)
        PUT /api/products/{id}/     - Update product (owner only)
        PATCH /api/products/{id}/   - Partial update (owner only)
        DELETE /api/products/{id}/  - Delete product (owner only)
    
    Query Parameters:
        ?category=5     - Filter by category ID
        ?status=ACTIVE  - Filter by status (admin/seller only)
        ?search=phone   - Search in name and description
        ?ordering=price - Order by field (price, -price, created_at, -created_at)
    
    Permission Logic:
        - List/Retrieve: Public (but filtered to ACTIVE only)
        - Create: Authenticated users
        - Update/Delete: Owner only (via IsAuthenticatedOrReadOnly)
    
    Business Rules:
        - Public only sees ACTIVE products
        - Sellers see their own products (any status) + all ACTIVE products
        - Admins see all products (for moderation)
    
    Filtering & Search:
        - DjangoFilterBackend: category, status filters
        - SearchFilter: name/description text search
        - OrderingFilter: sort by price, created_at
        - Results are paginated (configured in settings.py)
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at']  # Newest first by default
    
    def get_queryset(self):
        """
        Dynamic queryset based on user role - STRICT SEPARATION.
        
        Access Control:
        - Unauthenticated/Buyers: Only ACTIVE products from ALL sellers
        - Sellers: ONLY their own products (all statuses) - CANNOT see other sellers
        - Admins: All products (for moderation)
        
        Why strict separation?
        - Sellers manage only their inventory
        - Sellers cannot browse/copy competitor products
        - Clear business boundaries
        - Performance: sellers don't load all marketplace data
        - Security: sellers only access their data
        
        Database Optimization:
        - No select_related here because we use serializer optimization
        - Queryset is lean, let serializer handle prefetching
        """
        queryset = Product.objects.all()
        
        # Admin sees all products (for moderation)
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return queryset
        
        # Sellers: ONLY their own products (any status) - NO OTHER PRODUCTS
        # They use the seller dashboard, not buyer marketplace
        if self.request.user.is_authenticated and self.request.user.role == 'SELLER' and hasattr(self.request.user, 'seller'):
            return queryset.filter(seller=self.request.user.seller)
        
        # Unauthenticated users and Buyers: Only ACTIVE products (public marketplace)
        return queryset.filter(status='ACTIVE')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProductCreateSerializer
        return ProductSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsVerifiedSeller()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsVerifiedSeller(), IsOwnerOrReadOnly()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """Create product for current seller as DRAFT."""
        serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[IsVerifiedSeller, IsOwnerOrReadOnly])
    def submit_for_approval(self, request, pk=None):
        """
        Seller action: Submit product for admin approval.
        
        POST /api/products/{id}/submit_for_approval/
        
        Transition: DRAFT → PENDING_APPROVAL
        
        Business Rules:
        - Only verified sellers can submit
        - Only DRAFT products can be submitted
        - Triggers notification signal to admin
        """
        product = self.get_object()
        
        try:
            product.submit_for_approval()
            return Response({
                'message': 'Product submitted for approval.',
                'status': product.status
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """
        Admin action: Approve product and make it live.
        
        POST /api/products/{id}/approve/
        
        Transition: PENDING_APPROVAL → ACTIVE
        
        Business Rules:
        - Only admins can approve
        - Only PENDING_APPROVAL products can be approved
        - Triggers notification signal to seller
        """
        product = self.get_object()
        
        try:
            product.approve()
            return Response({
                'message': f'Product "{product.name}" approved and is now live.',
                'status': product.status
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def suspend(self, request, pk=None):
        """
        Admin action: Suspend product for policy violations.
        
        POST /api/products/{id}/suspend/
        Request body: {"reason": "Violates marketplace policy"}
        
        Transition: ACTIVE → SUSPENDED
        
        Business Rules:
        - Only admins can suspend
        - Only ACTIVE products can be suspended
        - Triggers notification signal to seller with reason
        """
        product = self.get_object()
        reason = request.data.get('reason', '')
        
        try:
            product.suspend(reason=reason)
            return Response({
                'message': f'Product "{product.name}" has been suspended.',
                'reason': reason,
                'status': product.status
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrReadOnly])
    def archive(self, request, pk=None):
        """
        Seller/Admin action: Archive product permanently.
        
        POST /api/products/{id}/archive/
        
        Transition: ANY → ARCHIVED
        
        Business Rules:
        - Owner or admin can archive
        - Used instead of delete when product has orders
        - Product becomes historical reference only
        """
        product = self.get_object()
        
        try:
            product.archive()
            return Response({
                'message': f'Product "{product.name}" has been archived.',
                'status': product.status
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsVerifiedSeller, IsOwnerOrReadOnly], parser_classes=[MultiPartParser, FormParser])
    def upload_image(self, request, pk=None):
        """
        Upload image for a product (max 6 images per product).
        
        POST /api/products/{id}/upload_image/
        
        Body (form-data):
            - image: Image file (required)
            - is_primary: Boolean (optional, default=False)
        
        Business Rules:
        - Only product owner can upload
        - Maximum 6 images per product
        - If is_primary=True, other images are set to False
        - If product has 0 images, first image is automatically primary
        - Returns list of all product images
        
        Error Responses:
        - 400: Maximum images limit reached (delete one first)
        - 400: Invalid image file
        - 403: Not product owner
        """
        product = self.get_object()
        
        serializer = ProductImageUploadSerializer(
            data=request.data,
            context={'product': product, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return all images for this product
        from .serializers import ProductImageSerializer
        images = ProductImage.objects.filter(product=product)
        return Response(
            ProductImageSerializer(images, many=True, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['delete'], permission_classes=[IsVerifiedSeller, IsOwnerOrReadOnly])
    def delete_image(self, request, pk=None):
        """
        Delete a product image.
        
        DELETE /api/products/{id}/delete_image/?image_id=123
        
        Query Parameters:
            - image_id: ID of the ProductImage to delete
        
        Business Rules:
        - Only product owner can delete
        - Cannot delete if it's the only image (optional rule)
        """
        product = self.get_object()
        image_id = request.query_params.get('image_id')
        
        if not image_id:
            return Response(
                {'error': 'image_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            image = ProductImage.objects.get(id=image_id, product=product)
            image.delete()
            
            # Return remaining images
            from .serializers import ProductImageSerializer
            images = ProductImage.objects.filter(product=product)
            return Response(
                ProductImageSerializer(images, many=True, context={'request': request}).data
            )
        except ProductImage.DoesNotExist:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )
