from rest_framework import serializers
from .models import Review, Report
from apps.orders.models import OrderItem


class ReviewSerializer(serializers.ModelSerializer):
    """
    Review serializer.
    """
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'order', 'product', 'product_name', 'seller',
            'reviewer', 'reviewer_name', 'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['id', 'reviewer', 'created_at']

    def validate(self, data):
        """Validate review creation rules."""
        user = self.context['request'].user
        order = data['order']
        product = data['product']
        seller = data.get('seller')

        # Check if user is the buyer
        if order.buyer != user:
            raise serializers.ValidationError("You can only review your own orders.")

        # Only delivered orders can be reviewed
        if order.status != 'DELIVERED':
            raise serializers.ValidationError("You can only review delivered orders.")

        # Product must be part of this order
        order_item = OrderItem.objects.filter(order=order, product=product).first()
        if order_item is None:
            raise serializers.ValidationError("You can only review products that were delivered in this order.")

        # Seller must match ordered item's seller (prevents payload tampering)
        if seller and order_item.seller_id != seller.id:
            raise serializers.ValidationError("Seller does not match the delivered product.")

        # Check if already reviewed
        if Review.objects.filter(order=order, product=product, reviewer=user).exists():
            raise serializers.ValidationError("You have already reviewed this delivered product.")

        data['seller'] = order_item.seller
        return data


class ReportSerializer(serializers.ModelSerializer):
    """
    Report serializer.
    """
    reporter_name = serializers.CharField(source='reporter.username', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'reporter_name', 'target_type', 'target_id',
            'reason', 'description', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'reporter', 'status', 'created_at']
