from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch, Q, Case, When, Value, IntegerField, Count, Min, Max
from django.db import transaction
from .models import Category, Product, ProductImage
from .serializers import (
    CategorySerializer, 
    ProductSerializer, 
    ProductCreateSerializer,
    ProductImageUploadSerializer
)
from apps.common.api import get_user_seller, model_field_available
from apps.common.permissions import IsVerifiedSeller, IsOwnerOrReadOnly


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Category viewset (read-only for all).
    
    GET /api/categories/ - List all active categories
    GET /api/categories/{id}/ - Get category details
    """
    queryset = Category.objects.filter(is_active=True).only('id', 'name', 'slug', 'is_active')
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
        image_prefetch = Prefetch(
            'images',
            queryset=ProductImage.objects.only('id', 'image', 'is_primary', 'position', 'product_id').order_by('position', 'id')
        )
        queryset = Product.objects.select_related('seller', 'category').prefetch_related(image_prefetch)
        if not model_field_available(Product, 'attributes'):
            queryset = queryset.defer('attributes')

        # Admin sees all products (for moderation)
        if self.request.user.is_authenticated and self.request.user.is_staff:
            base_queryset = queryset
        
        # Sellers: ONLY their own products (any status) - NO OTHER PRODUCTS
        # They use the seller dashboard, not buyer marketplace
        elif self.request.user.is_authenticated and self.request.user.role == 'SELLER':
            seller = get_user_seller(self.request.user)
            if seller is None:
                base_queryset = queryset.none()
            else:
                base_queryset = queryset.filter(seller=seller)
        else:
            # Unauthenticated users and Buyers: Only ACTIVE products (public marketplace)
            base_queryset = queryset.filter(status='ACTIVE')

        # Enhanced discovery filters for marketplace browsing.
        queryset = base_queryset
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        in_stock = self.request.query_params.get('in_stock')
        category_slug = self.request.query_params.get('category_slug')
        q = self.request.query_params.get('q')

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if in_stock and in_stock.lower() in ['1', 'true', 'yes']:
            queryset = queryset.filter(stock__gt=0)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        if q:
            queryset = queryset.filter(
                Q(name__icontains=q)
                | Q(description__icontains=q)
                | Q(category__name__icontains=q)
                | Q(seller__store_name__icontains=q)
            ).annotate(
                relevance_score=Case(
                    When(name__iexact=q, then=Value(100)),
                    When(name__istartswith=q, then=Value(70)),
                    When(description__icontains=q, then=Value(30)),
                    default=Value(10),
                    output_field=IntegerField(),
                )
            ).order_by('-relevance_score', '-created_at')
        
        return queryset
    
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

    @action(detail=True, methods=['post'], permission_classes=[IsVerifiedSeller, IsOwnerOrReadOnly])
    def set_primary_image(self, request, pk=None):
        product = self.get_object()
        try:
            image = ProductImage.objects.get(pk=request.data.get('image_id'), product=product)
        except ProductImage.DoesNotExist:
            return Response({'error': 'Image not found.'}, status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            product.images.update(is_primary=False)
            image.is_primary = True
            image.save(update_fields=['is_primary'])
        from .serializers import ProductImageSerializer
        return Response(ProductImageSerializer(product.images.all(), many=True, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsVerifiedSeller, IsOwnerOrReadOnly])
    def reorder_images(self, request, pk=None):
        product = self.get_object()
        try:
            image_ids = [int(value) for value in request.data.get('image_ids', [])]
        except (TypeError, ValueError):
            return Response({'error': 'image_ids must be an ordered list of integers.'}, status=status.HTTP_400_BAD_REQUEST)
        existing = list(product.images.values_list('id', flat=True))
        if len(image_ids) != len(set(image_ids)) or set(image_ids) != set(existing):
            return Response({'error': 'image_ids must contain every product image exactly once.'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            for position, image_id in enumerate(image_ids):
                ProductImage.objects.filter(pk=image_id, product=product).update(position=position)
        from .serializers import ProductImageSerializer
        return Response(ProductImageSerializer(product.images.all(), many=True, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def facets(self, request):
        """Return discovery facets for search UI (categories, stock, price range)."""
        queryset = self.get_queryset()

        category_buckets = queryset.values(
            'category_id', 'category__name', 'category__slug'
        ).annotate(count=Count('id')).order_by('-count', 'category__name')

        price_stats = queryset.aggregate(min_price=Min('price'), max_price=Max('price'))

        return Response(
            {
                'categories': [
                    {
                        'id': bucket['category_id'],
                        'name': bucket['category__name'] or 'Uncategorized',
                        'slug': bucket['category__slug'],
                        'count': bucket['count'],
                    }
                    for bucket in category_buckets
                ],
                'stock': {
                    'in_stock': queryset.filter(stock__gt=0).count(),
                    'out_of_stock': queryset.filter(stock=0).count(),
                },
                'price_range': {
                    'min': price_stats['min_price'],
                    'max': price_stats['max_price'],
                },
            }
        )
