from rest_framework import serializers
from .models import Order, OrderItem, InventoryReservation, PaymentAttempt, OrderFulfillment
from apps.products.serializers import ProductSerializer
from apps.common.mixins import ImageURLMixin
from django.db import transaction
from django.utils import timezone
from apps.products.models import Product
from decimal import Decimal


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
            'cancelled_quantity', 'active_quantity', 'refunded_amount', 'cancellation_reason',
            'created_at'
        ]
        read_only_fields = ['id', 'price_snapshot', 'cancelled_quantity', 'active_quantity', 'refunded_amount', 'cancellation_reason', 'created_at']
    
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
            'product_subtotal', 'delivery_fee', 'origin_pickup_fee', 'inter_district_fee',
            'destination_delivery_fee', 'origin_pickup_required', 'destination_delivery_required', 'delivery_service',
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
    items = OrderItemCreateSerializer(many=True, write_only=True)
    delivery_zone_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'status',
            'order_type', 'po_number', 'company_name', 'company_tax_id', 'payment_terms',
            'procurement_notes', 'requested_fulfillment_date', 'items',
            'total_amount', 'product_subtotal', 'delivery_fee', 'shipping_address', 'delivery_zone',
            'delivery_zone_id', 'delivery_instructions', 'origin_pickup_required',
            'destination_delivery_required', 'delivery_service', 'origin_pickup_fee',
            'inter_district_fee', 'destination_delivery_fee'
        ]
        read_only_fields = ['id', 'status', 'total_amount', 'product_subtotal', 'delivery_fee',
                            'delivery_zone', 'delivery_service', 'origin_pickup_fee',
                            'inter_district_fee', 'destination_delivery_fee']

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
        items_data = validated_data.pop('items')
        zone_id = validated_data.pop('delivery_zone_id')
        from .delivery import quote_delivery
        quote = quote_delivery(
            zone_id=zone_id,
            origin_pickup_required=validated_data.get('origin_pickup_required', False),
            destination_delivery_required=validated_data.get('destination_delivery_required', False),
        )
        if not items_data:
            raise serializers.ValidationError({'items': 'At least one item is required.'})

        # Merge duplicate product lines so stock and totals have one clear truth.
        quantities = {}
        for item in items_data:
            product_id = item['product'].id
            quantities[product_id] = quantities.get(product_id, 0) + item['quantity']

        with transaction.atomic():
            products = {
                product.id: product
                for product in Product.objects.select_for_update().filter(id__in=quantities)
            }
            total = Decimal('0.00')
            for product_id, quantity in quantities.items():
                product = products[product_id]
                if product.status != 'ACTIVE':
                    raise serializers.ValidationError({'items': f'{product.name} is not available.'})
                if product.available_stock < quantity:
                    raise serializers.ValidationError({
                        'items': f'Insufficient stock for {product.name}. Available: {product.available_stock}'
                    })
                total += product.price * quantity

            validated_data['buyer'] = self.context['request'].user
            validated_data['product_subtotal'] = total
            validated_data['delivery_fee'] = quote['delivery_fee']
            validated_data['origin_pickup_fee'] = quote['origin_pickup_fee']
            validated_data['inter_district_fee'] = quote['inter_district_fee']
            validated_data['destination_delivery_fee'] = quote['destination_delivery_fee']
            validated_data['delivery_service'] = quote['delivery_service']
            validated_data['delivery_zone'] = quote['zone_name']
            validated_data['total_amount'] = total + quote['delivery_fee']
            order = Order.objects.create(**validated_data)
            expires_at = timezone.now() + timezone.timedelta(minutes=20)
            for product_id, quantity in quantities.items():
                product = products[product_id]
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    seller=product.seller,
                    quantity=quantity,
                    price_snapshot=product.price,
                )
                product.reserved_stock += quantity
                product.save(update_fields=['reserved_stock', 'updated_at'])
                InventoryReservation.objects.create(
                    order=order, product=product, quantity=quantity, expires_at=expires_at
                )
            for seller_id in order.items.values_list('seller_id', flat=True).distinct():
                OrderFulfillment.objects.create(
                    order=order,
                    seller_id=seller_id,
                    fulfill_by=timezone.now() + timezone.timedelta(days=2),
                )
            return order


class PaymentAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAttempt
        fields = ['id', 'order', 'provider', 'provider_reference', 'amount', 'currency', 'status', 'failure_code', 'created_at', 'updated_at']
        read_only_fields = fields


class OrderFulfillmentSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.store_name', read_only=True)

    class Meta:
        model = OrderFulfillment
        fields = ['id', 'order', 'seller', 'seller_name', 'status', 'carrier', 'tracking_number', 'fulfill_by', 'accepted_at', 'ready_at', 'handed_over_at', 'created_at', 'updated_at']
        read_only_fields = fields
