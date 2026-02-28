from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.sellers.models import Seller

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    User serializer with password handling.
    """
    password = serializers.CharField(write_only=True)
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'password', 'profile_picture', 'profile_picture_url', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'is_active', 'profile_picture_url']
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
        return None

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'BUYER')
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Public user profile (no sensitive data).
    """
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'is_superuser', 'profile_picture_url', 'date_joined']
        read_only_fields = fields
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
        return None
