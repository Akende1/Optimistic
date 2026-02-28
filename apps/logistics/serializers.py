from rest_framework import serializers
from .models import Delivery, DeliveryPartner, ZambianLocation


class DeliveryPartnerSerializer(serializers.ModelSerializer):
    """
    Delivery partner serializer (public view).
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    verification_status = serializers.SerializerMethodField()
    
    class Meta:
        model = DeliveryPartner
        fields = [
            'id', 'user', 'user_username', 'name', 'phone', 'email',
            'partner_type', 'service_area', 'vehicle_type',
            'verified', 'is_active', 'verification_status', 'created_at'
        ]
        read_only_fields = ['id', 'verified', 'created_at']
    
    def get_verification_status(self, obj):
        if obj.verified:
            return 'Verified'
        return 'Pending Verification'


class DeliveryPartnerRegistrationSerializer(serializers.ModelSerializer):
    """
    Courier registration serializer for onboarding.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    username = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = DeliveryPartner
        fields = [
            'username', 'password', 'name', 'phone', 'email',
            'partner_type', 'service_area', 'vehicle_type', 'id_number'
        ]
    
    def create(self, validated_data):
        from apps.accounts.models import User
        
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        
        # Create user account with COURIER role
        user = User.objects.create_user(
            username=username,
            password=password,
            email=validated_data.get('email', ''),
            role='COURIER',  # Courier role enforces separation of concerns
            is_active=True
        )
        
        # Create delivery partner profile
        partner = DeliveryPartner.objects.create(
            user=user,
            **validated_data
        )
        
        return partner


class ZambianLocationSerializer(serializers.ModelSerializer):
    """
    Location serializer for provinces, cities, and zones.
    """
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = ZambianLocation
        fields = [
            'id', 'name', 'location_type', 'parent', 'parent_name',
            'full_address', 'delivery_base_cost', 'is_active'
        ]
        read_only_fields = ['id']
    
    def get_full_address(self, obj):
        return obj.get_full_address()


class DeliverySerializer(serializers.ModelSerializer):
    """
    Delivery tracking serializer.
    """
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True)

    class Meta:
        model = Delivery
        fields = [
            'id', 'order', 'order_id', 'partner', 'partner_name',
            'pickup_address', 'delivery_address', 'delivery_fee',
            'status', 'notes', 'created_at', 'delivered_at'
        ]
        read_only_fields = ['id', 'created_at', 'delivered_at']
