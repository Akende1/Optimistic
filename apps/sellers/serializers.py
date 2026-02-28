from rest_framework import serializers
from .models import Seller
from apps.accounts.serializers import UserProfileSerializer


class SellerSerializer(serializers.ModelSerializer):
    """
    Seller profile serializer.
    """
    user = UserProfileSerializer(read_only=True)
    profile_image_url = serializers.SerializerMethodField()
    banner_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Seller
        fields = [
            'id', 'user', 'store_name', 'phone', 'description',
            'profile_image', 'profile_image_url',
            'banner_image', 'banner_image_url',
            'verified', 'created_at'
        ]
        read_only_fields = ['id', 'verified', 'created_at']
    
    def get_profile_image_url(self, obj):
        if obj.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None
    
    def get_banner_image_url(self, obj):
        if obj.banner_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.banner_image.url)
            return obj.banner_image.url
        return None


class SellerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating seller profile.
    """
    class Meta:
        model = Seller
        fields = ['store_name', 'phone', 'description']

    def create(self, validated_data):
        user = self.context['request'].user
        seller = Seller.objects.create(user=user, **validated_data)
        # Update user role to SELLER
        user.role = 'SELLER'
        user.save()
        return seller


class SellerUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating seller profile (including images).
    """
    class Meta:
        model = Seller
        fields = ['store_name', 'phone', 'description', 'profile_image', 'banner_image']
