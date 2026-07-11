from rest_framework import serializers
from django.db import transaction
from .models import Seller, SellerVerification
from apps.accounts.serializers import UserProfileSerializer
from apps.common.api import SCHEMA_DRIFT_ERROR, model_field_available


class SellerSerializer(serializers.ModelSerializer):
    """
    Seller profile serializer.
    """
    user = UserProfileSerializer(read_only=True)
    primary_location = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()
    banner_image_url = serializers.SerializerMethodField()
    primary_location_name = serializers.SerializerMethodField()
    primary_location_type = serializers.SerializerMethodField()
    primary_location_full = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    verification_status = serializers.CharField(read_only=True)
    verified_at = serializers.DateTimeField(read_only=True)
    verified_by_username = serializers.CharField(source='verified_by.username', read_only=True)
    kyc_status = serializers.SerializerMethodField()
    kyc_rejection_reason = serializers.SerializerMethodField()

    class Meta:
        model = Seller
        fields = [
            'id', 'user', 'store_name', 'phone', 'description',
            'business_type', 'business_name', 'business_registration_number', 'tax_pin',
            'physical_address', 'town_city', 'province',
            'payout_method', 'payout_provider', 'payout_account_name', 'payout_account_number', 'payout_account_verified',
            'primary_location', 'primary_location_name', 'primary_location_type', 'primary_location_full',
            'profile_image', 'profile_image_url',
            'banner_image', 'banner_image_url',
            'verified', 'verification_status', 'verified_at', 'verified_by_username',
            'completion_percentage', 'kyc_status', 'kyc_rejection_reason', 'created_at'
        ]
        read_only_fields = ['id', 'verified', 'verification_status', 'verified_at', 'verified_by_username', 'payout_account_verified', 'completion_percentage', 'kyc_status', 'kyc_rejection_reason', 'created_at']
    
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

    def get_primary_location(self, obj):
        if not model_field_available(Seller, 'primary_location'):
            return None
        return getattr(obj, 'primary_location_id', None)

    def get_primary_location_name(self, obj):
        location = self._get_primary_location(obj)
        return location.name if location else ''

    def get_primary_location_type(self, obj):
        location = self._get_primary_location(obj)
        return location.location_type if location else ''

    def get_primary_location_full(self, obj):
        location = self._get_primary_location(obj)
        if location:
            return location.get_full_address()
        return ''

    def get_completion_percentage(self, obj):
        return obj.get_completion_percentage()

    def get_kyc_status(self, obj):
        verification = getattr(obj, 'kyc_documents', None)
        if verification is None:
            return None
        return verification.status

    def get_kyc_rejection_reason(self, obj):
        verification = getattr(obj, 'kyc_documents', None)
        if verification is None:
            return ''
        return verification.rejection_reason

    def _get_primary_location(self, obj):
        if not model_field_available(Seller, 'primary_location'):
            return None
        try:
            return obj.primary_location
        except Exception:
            return None


class SellerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating seller profile.
    """
    class Meta:
        model = Seller
        fields = ['store_name', 'phone', 'description', 'primary_location']

    def validate_primary_location(self, value):
        if not model_field_available(Seller, 'primary_location'):
            raise serializers.ValidationError(SCHEMA_DRIFT_ERROR)
        if value and not value.is_active:
            raise serializers.ValidationError('Selected location is inactive.')
        return value

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
        fields = [
            'store_name', 'phone', 'description',
            'business_type', 'business_name', 'business_registration_number', 'tax_pin',
            'physical_address', 'town_city', 'province',
            'payout_method', 'payout_provider', 'payout_account_name', 'payout_account_number',
            'primary_location', 'profile_image', 'banner_image'
        ]

    def validate_primary_location(self, value):
        if not model_field_available(Seller, 'primary_location'):
            raise serializers.ValidationError(SCHEMA_DRIFT_ERROR)
        if value and not value.is_active:
            raise serializers.ValidationError('Selected location is inactive.')
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        sensitive = {'business_type','business_name','business_registration_number','tax_pin',
                     'physical_address','primary_location','payout_method','payout_provider',
                     'payout_account_name','payout_account_number'}
        changed = any(field in validated_data and getattr(instance, field) != value
                      for field, value in validated_data.items() if field in sensitive)
        instance = super().update(instance, validated_data)
        if changed and instance.verified:
            instance.verified = False
            instance.verification_status = 'PENDING'
            instance.payout_account_verified = False
            instance.verification_notes = 'Identity-sensitive profile information changed; re-verification required.'
            instance.save(update_fields=['verified','verification_status','payout_account_verified','verification_notes'])
            instance.products.filter(status='ACTIVE').update(status='SUSPENDED')
        return instance


class SellerVerificationSerializer(serializers.ModelSerializer):
    """Seller KYC submission and status serializer."""
    seller = serializers.PrimaryKeyRelatedField(read_only=True)
    seller_name = serializers.CharField(source='seller.store_name', read_only=True)
    seller_verified = serializers.BooleanField(source='seller.verified', read_only=True)
    seller_verification_status = serializers.CharField(source='seller.verification_status', read_only=True)
    government_id_front_url = serializers.SerializerMethodField()
    government_id_back_url = serializers.SerializerMethodField()
    selfie_with_id_url = serializers.SerializerMethodField()
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True)
    attests_information_accurate = serializers.BooleanField(write_only=True)
    consents_to_identity_checks = serializers.BooleanField(write_only=True)

    class Meta:
        model = SellerVerification
        fields = [
            'id', 'seller', 'seller_name', 'seller_verified', 'seller_verification_status',
            'government_id_type', 'government_id_number', 'government_id_front', 'government_id_front_url',
            'government_id_back', 'government_id_back_url', 'selfie_with_id', 'selfie_with_id_url',
            'status', 'rejection_reason', 'submitted_at', 'reviewed_at', 'reviewed_by', 'reviewed_by_username'
            , 'attests_information_accurate', 'consents_to_identity_checks'
        ]
        read_only_fields = [
            'id', 'seller', 'seller_name', 'seller_verified', 'seller_verification_status',
            'status', 'rejection_reason', 'submitted_at', 'reviewed_at', 'reviewed_by', 'reviewed_by_username',
            'government_id_front_url', 'government_id_back_url', 'selfie_with_id_url'
        ]

    def get_government_id_front_url(self, obj):
        if obj.government_id_front:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.government_id_front.url) if request else obj.government_id_front.url
        return None

    def get_government_id_back_url(self, obj):
        if obj.government_id_back:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.government_id_back.url) if request else obj.government_id_back.url
        return None

    def get_selfie_with_id_url(self, obj):
        if obj.selfie_with_id:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.selfie_with_id.url) if request else obj.selfie_with_id.url
        return None

    def validate(self, attrs):
        attrs = super().validate(attrs)
        seller = self.context.get('seller') or getattr(self.instance, 'seller', None)
        if seller and seller.verified and seller.verification_status == 'VERIFIED':
            raise serializers.ValidationError('Verified sellers cannot overwrite approved KYC documents.')
        if not attrs.pop('attests_information_accurate', False):
            raise serializers.ValidationError({'attests_information_accurate': 'You must attest that the information is accurate.'})
        if not attrs.pop('consents_to_identity_checks', False):
            raise serializers.ValidationError({'consents_to_identity_checks': 'Consent is required to perform identity checks.'})
        number = (attrs.get('government_id_number') or getattr(self.instance, 'government_id_number', '')).strip().upper()
        if len(number) < 5:
            raise serializers.ValidationError({'government_id_number': 'Enter a valid government ID number.'})
        attrs['government_id_number'] = number
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        seller = self.context.get('seller')
        if seller is None:
            raise serializers.ValidationError({'seller': 'Seller context is required.'})

        verification, _ = SellerVerification.objects.update_or_create(
            seller=seller,
            defaults=validated_data,
        )
        verification.submit_for_review()
        return verification

    @transaction.atomic
    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        instance.submit_for_review()
        return instance


class SellerVerificationReviewSerializer(serializers.Serializer):
    """Admin review action serializer."""
    action = serializers.ChoiceField(choices=['APPROVE', 'REJECT'])
    reason = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs['action'] == 'REJECT' and not attrs.get('reason'):
            raise serializers.ValidationError({'reason': 'Reason is required when rejecting verification.'})
        return attrs
