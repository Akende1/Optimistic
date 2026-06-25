from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.serializers import ProductSerializer
from apps.common.mixins import ImageURLMixin


class OrderItemSerializer(ImageURLMixin, serializers.ModelSerializer):
    """
    OrderItem serializer with product and seller details.
    
    Purpose: Display line items in order details
    
    Read-only fields:
    - product_name, product_image: Display cached from product
    - seller_name: Display cached from seller
    - subtotal: Calculated property (price × quantity)
    """
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    seller_name = serializers.CharField(source='seller.store_name', read_only=True)
    seller_id = serializers.IntegerField(source='seller.id', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_name', 'product_image',
            'seller', 'seller_id', 'seller_name',
            'quantity', 'price_snapshot', 'subtotal',
            'created_at'
        ]
        read_only_fields = ['id', 'price_snapshot', 'created_at']
    
    def get_product_image(self, obj):
        """Get primary product image URL."""
        if obj.product and hasattr(obj.product, 'images'):
            primary_image = obj.product.images.filter(is_primary=True).first()
            if primary_image:
                return self.get_image_url(primary_image.image)
        return None


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating order items.
    
    Auto-populates seller and price_snapshot from product.
    Validates stock availability.
    """
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']
    
    def validate(self, data):
        """Validate stock availability."""
        product = data.get('product')
        quantity = data.get('quantity')
        
        if product.stock < quantity:
            raise serializers.ValidationError(
                f"Insufficient stock for {product.name}. Available: {product.stock}"
            )
        
        if product.status != 'ACTIVE':
            raise serializers.ValidationError(
                f"Product {product.name} is not available for purchase"
            )
        
        return data


class OrderSerializer(serializers.ModelSerializer):
    """
    Order serializer with delivery information and order items.
    """
    buyer_username = serializers.CharField(source='buyer.username', read_only=True)
    delivery_partner_name = serializers.CharField(source='delivery_partner.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_confirm_delivery = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    calculated_total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'buyer', 'buyer_username', 'order_type', 'po_number', 'company_name', 'company_tax_id',
            'payment_terms', 'procurement_notes', 'requested_fulfillment_date',
            'total_amount', 'calculated_total',
            'status', 'status_display',
            'shipping_address', 'delivery_zone', 'delivery_instructions',
            'delivery_partner', 'delivery_partner_name',
            'delivered_at', 'confirmed_by_buyer', 'can_confirm_delivery',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'buyer', 'status', 'delivered_at', 'confirmed_by_buyer', 'created_at', 'updated_at']
    
    def get_can_confirm_delivery(self, obj):
        """Check if buyer can confirm delivery (order is IN_TRANSIT and not yet confirmed)."""
        return obj.status == 'IN_TRANSIT' and not obj.confirmed_by_buyer
    
    def get_calculated_total(self, obj):
        """Calculate total from order items (for validation)."""
        return obj.calculate_total()


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new orders with delivery details.
    """
    class Meta:
        model = Order
        fields = [
            'order_type', 'po_number', 'company_name', 'company_tax_id', 'payment_terms',
            'procurement_notes', 'requested_fulfillment_date',
            'total_amount', 'shipping_address', 'delivery_zone', 'delivery_instructions'
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        order_type = attrs.get('order_type', 'RETAIL')
        if order_type == 'PURCHASE_ORDER':
            if not attrs.get('po_number'):
                raise serializers.ValidationError({'po_number': 'PO number is required for purchase-order checkout.'})
            if not attrs.get('company_name'):
                raise serializers.ValidationError({'company_name': 'Company name is required for purchase-order checkout.'})
        return attrs
    
    def create(self, validated_data):
        # Set buyer from request user
        validated_data['buyer'] = self.context['request'].user
        return super().create(validated_data)
