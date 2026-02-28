from rest_framework import serializers
from .models import Review, Report


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

        # Check if user is the buyer
        if order.buyer != user:
            raise serializers.ValidationError("You can only review your own orders.")

        # Check if already reviewed
        if Review.objects.filter(order=order, reviewer=user).exists():
            raise serializers.ValidationError("You have already reviewed this order.")

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
