from rest_framework import serializers
from .models import Category, Product, ProductImage
from .category_specs import get_category_attribute_schema, normalize_and_validate_attributes
from apps.common.mixins import ImageURLMixin, SchemaDriftMixin
from apps.sellers.utils import get_user_seller


class CategorySerializer(SchemaDriftMixin, serializers.ModelSerializer):
    """
    Category serializer.
    """
    attribute_schema = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'is_active', 'attribute_schema']
        read_only_fields = ['id']

    def get_attribute_schema(self, obj):
        return get_category_attribute_schema(obj)


class ProductImageSerializer(ImageURLMixin, serializers.ModelSerializer):
    """
    Product image serializer with full URL.
    """
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url', 'is_primary', 'position']
        read_only_fields = ['id', 'position']


class ProductSerializer(SchemaDriftMixin, serializers.ModelSerializer):
    """
    Product serializer for API responses and updates.
    
    Purpose: Convert Product model to/from JSON for API communication
    
    Design Decisions:
    - Nested display: category_name, seller_name (easier for frontend)
    - Read-only images: Prevents image upload via product endpoint
    - Status read-only: Only admins can change status (via admin panel)
    
    Why category_name instead of full CategorySerializer?
    - Lighter payload: Just the name, not entire object
    - Good enough: Frontend only needs to display category name
    - Can always expand to full object if needed
    
    Read-Only Fields:
    - id: Database generates this (auto-increment)
    - seller: Set from request.user in view's perform_create()
    - status: Only admin can change (approval workflow)
    - created_at/updated_at: Database manages timestamps
    
    Write Fields (Client can set):
    - category: Category ID to assign product to
    - name: Product title
    - description: Full product description
    - price: Product price in ZMW
    - stock: Available quantity
    
    Validation (happens automatically):
    - price: Must be ≥ 0 (model validation)
    - stock: Must be ≥ 0 (PositiveIntegerField)
    - name: Max 150 chars (model field limit)
    - category: Must be valid Category ID (ForeignKey)
    """
    # Nested data: Show more than just IDs
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_name = serializers.CharField(source='seller.store_name', read_only=True)
    attributes = serializers.JSONField(required=False)
    available_stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'seller_name', 'category', 'category_name',
            'name', 'description', 'price', 'stock', 'available_stock', 'attributes', 'status',
            'weight_kg', 'length_cm', 'width_cm', 'height_cm', 'shipping_class', 'tax_category',
            'images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'seller', 'status', 'created_at', 'updated_at']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        category = attrs.get('category') or getattr(self.instance, 'category', None)

        if 'attributes' in attrs:
            self.check_field_available(Product, 'attributes')
            normalized, errors = normalize_and_validate_attributes(category, attrs.get('attributes'))
            if errors:
                raise serializers.ValidationError({'attributes': errors})
            attrs['attributes'] = normalized

        return attrs
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Ensure attributes is always a dictionary even if null in DB
        ret['attributes'] = ret.get('attributes') or {}
        return ret


class ProductCreateSerializer(SchemaDriftMixin, serializers.ModelSerializer):
    """
    Serializer for creating products (sellers only).
    """
    attributes = serializers.JSONField(required=False, default=dict)

    class Meta:
        model = Product
        fields = ['id', 'category', 'name', 'description', 'price', 'stock', 'attributes',
                  'weight_kg', 'length_cm', 'width_cm', 'height_cm', 'shipping_class', 'tax_category']
        read_only_fields = ['id']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        self.check_field_available(Product, 'attributes')
        normalized, errors = normalize_and_validate_attributes(attrs.get('category'), attrs.get('attributes'))
        if errors:
            raise serializers.ValidationError({'attributes': errors})
        attrs['attributes'] = normalized
        return attrs
    
    def create(self, validated_data):
        seller = get_user_seller(self.context['request'].user)
        if seller is None:
            raise serializers.ValidationError({'seller': 'Seller profile not found for the current user.'})
        product = Product.objects.create(
            seller=seller,
            status='DRAFT',
            **validated_data
        )
        return product


class ProductImageUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading product images.
    
    Validation Rules:
    - Maximum 6 images per product
    - Image file required
    - Only one primary image allowed
    """
    class Meta:
        model = ProductImage
        fields = ['image', 'is_primary']
    
    def validate(self, attrs):
        """Validate max images per product."""
        product = self.context['product']
        existing_count = ProductImage.objects.filter(product=product).count()
        
        if existing_count >= ProductImage.MAX_IMAGES_PER_PRODUCT:
            raise serializers.ValidationError(
                f'Product can have maximum {ProductImage.MAX_IMAGES_PER_PRODUCT} images. '
                f'Current count: {existing_count}. Please delete an existing image first.'
            )
        
        return attrs
    
    def create(self, validated_data):
        product = self.context['product']
        
        # If this is marked as primary, unset other primary images
        if validated_data.get('is_primary', False):
            ProductImage.objects.filter(product=product, is_primary=True).update(is_primary=False)
        
        return ProductImage.objects.create(product=product, position=product.images.count(), **validated_data)
