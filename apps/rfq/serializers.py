from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.common.api import get_user_seller
from .models import RfqRequest, RfqItem, SupplierQuote, SupplierQuoteItem


class RfqItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RfqItem
        fields = ['id', 'product', 'category', 'description', 'quantity', 'target_price', 'unit']
        read_only_fields = ['id']


class SupplierQuoteItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = SupplierQuoteItem
        fields = ['id', 'rfq_item', 'product', 'description', 'quantity', 'moq', 'unit_price', 'subtotal']
        read_only_fields = ['id', 'subtotal']

    def get_subtotal(self, obj):
        return obj.subtotal


class SupplierQuoteSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.store_name', read_only=True)
    items = SupplierQuoteItemSerializer(many=True)

    class Meta:
        model = SupplierQuote
        fields = [
            'id', 'rfq', 'seller', 'seller_name', 'status', 'lead_time_days', 'notes',
            'valid_until', 'total_amount', 'submitted_at', 'items'
        ]
        read_only_fields = ['id', 'seller', 'seller_name', 'status', 'total_amount', 'submitted_at']

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        seller = self.context.get('seller')
        if seller is None:
            raise serializers.ValidationError({'seller': 'Seller profile is required.'})

        quote = SupplierQuote.objects.create(seller=seller, **validated_data)
        total = Decimal('0.00')
        for item_data in items_data:
            item = SupplierQuoteItem.objects.create(quote=quote, **item_data)
            total += item.subtotal

        quote.total_amount = total
        quote.status = 'SUBMITTED'
        quote.save(update_fields=['total_amount', 'status'])
        return quote


class RfqRequestSerializer(serializers.ModelSerializer):
    items = RfqItemSerializer(many=True)
    quotes_count = serializers.IntegerField(source='quotes.count', read_only=True)

    class Meta:
        model = RfqRequest
        fields = [
            'id', 'buyer', 'title', 'description', 'status', 'incoterm', 'delivery_location',
            'is_sample_required', 'response_deadline', 'desired_delivery_date', 'awarded_quote',
            'created_at', 'updated_at', 'items', 'quotes_count'
        ]
        read_only_fields = ['id', 'buyer', 'status', 'awarded_quote', 'created_at', 'updated_at', 'quotes_count']

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        rfq = RfqRequest.objects.create(**validated_data)
        for item_data in items_data:
            RfqItem.objects.create(rfq=rfq, **item_data)
        return rfq


class RfqAwardSerializer(serializers.Serializer):
    quote_id = serializers.IntegerField()

    def validate_quote_id(self, value):
        rfq = self.context['rfq']
        if not rfq.quotes.filter(id=value, status='SUBMITTED').exists():
            raise serializers.ValidationError('Quote does not exist for this RFQ or is not in submitted state.')
        return value
