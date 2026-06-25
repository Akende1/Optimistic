from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify
from apps.sellers.models import Seller
from apps.accounts.models import BuyerAddress

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Minimal signup serializer for fast onboarding.
    """
    full_name = serializers.CharField(write_only=True, max_length=150)
    phone_number = serializers.CharField(write_only=True, max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=['BUYER', 'SELLER', 'BOTH'], default='BUYER')
    seller_type = serializers.ChoiceField(choices=['INDIVIDUAL', 'BUSINESS'], required=False, allow_null=True)
    shop_name = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=100)
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'phone_number', 'email', 'password', 'confirm_password',
            'role', 'seller_type', 'shop_name', 'profile_picture', 'profile_picture_url',
            'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'is_active', 'profile_picture_url']
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
        return None

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return normalized

    def validate_phone_number(self, value):
        normalized = value.strip()
        if User.objects.filter(phone_number=normalized).exists():
            raise serializers.ValidationError('An account with this phone number already exists.')
        return normalized

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})

        if attrs['role'] in ['SELLER', 'BOTH']:
            if not attrs.get('seller_type'):
                raise serializers.ValidationError({'seller_type': 'Seller type is required for seller accounts.'})
            if not attrs.get('shop_name'):
                raise serializers.ValidationError({'shop_name': 'Shop name is required for seller accounts.'})

        return attrs

    @staticmethod
    def _generate_username(email):
        base = slugify(email.split('@')[0])[:24] or 'user'
        candidate = base
        counter = 1
        while User.objects.filter(username=candidate).exists():
            suffix = str(counter)
            candidate = f"{base[: max(1, 24 - len(suffix))]}{suffix}"
            counter += 1
        return candidate

    @transaction.atomic
    def create(self, validated_data):
        full_name = validated_data.pop('full_name').strip()
        phone_number = validated_data.pop('phone_number').strip()
        password = validated_data.pop('password')
        validated_data.pop('confirm_password', None)
        seller_type = validated_data.pop('seller_type', None)
        shop_name = (validated_data.pop('shop_name', '') or '').strip()

        email = validated_data['email'].strip().lower()
        role = validated_data.get('role', 'BUYER')
        if role == 'BOTH':
            role = 'SELLER'
        username = self._generate_username(email)

        name_parts = full_name.split(None, 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            phone_verified=False,
        )

        if role == 'SELLER':
            business_type = 'SOLE_TRADER' if seller_type == 'INDIVIDUAL' else 'COMPANY'
            Seller.objects.create(
                user=user,
                store_name=shop_name,
                phone=phone_number,
                business_type=business_type,
                verification_status='PENDING',
                verified=False,
            )

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Public user profile (no sensitive data).
    """
    profile_picture_url = serializers.SerializerMethodField()
    phone_verified = serializers.BooleanField(read_only=True)
    phone_verified_at = serializers.DateTimeField(read_only=True)
    email_verified = serializers.BooleanField(read_only=True)
    email_verified_at = serializers.DateTimeField(read_only=True)
    seller_verified = serializers.SerializerMethodField()
    seller_verification_status = serializers.SerializerMethodField()
    seller_completion_percentage = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    buyer_address_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'role', 'status', 'is_superuser', 'phone_number', 'phone_verified', 'phone_verified_at',
            'email', 'email_verified', 'email_verified_at',
            'profile_picture_url', 'seller_verified', 'seller_verification_status', 'seller_completion_percentage',
            'buyer_address_count', 'date_joined'
        ]
        read_only_fields = fields
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
        return None

    def get_seller_verified(self, obj):
        seller = getattr(obj, 'seller', None)
        return seller.verified if seller else False

    def get_seller_verification_status(self, obj):
        seller = getattr(obj, 'seller', None)
        return seller.verification_status if seller else None

    def get_seller_completion_percentage(self, obj):
        seller = getattr(obj, 'seller', None)
        return seller.get_completion_percentage() if seller else None

    def get_full_name(self, obj):
        full_name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return full_name or obj.username

    def get_buyer_address_count(self, obj):
        return obj.addresses.count()


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=20)
    email = serializers.EmailField(required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'email']

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('Another account already uses this email.')
        return normalized

    def validate_phone_number(self, value):
        normalized = value.strip()
        if not normalized:
            return normalized
        if User.objects.filter(phone_number=normalized).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('Another account already uses this phone number.')
        return normalized

    def update(self, instance, validated_data):
        new_email = validated_data.get('email', instance.email)
        new_phone = validated_data.get('phone_number', instance.phone_number)

        email_changed = new_email != instance.email
        phone_changed = new_phone != instance.phone_number

        for field, value in validated_data.items():
            setattr(instance, field, value)

        # Changing contact channels requires re-verification for trust controls.
        if email_changed:
            instance.email_verified = False
            instance.email_verified_at = None
        if phone_changed:
            instance.phone_verified = False
            instance.phone_verified_at = None

        if email_changed or phone_changed:
            instance.status = 'REGISTERED'

        update_fields = list(validated_data.keys())
        if email_changed:
            update_fields.extend(['email_verified', 'email_verified_at'])
        if phone_changed:
            update_fields.extend(['phone_verified', 'phone_verified_at'])
        if email_changed or phone_changed:
            update_fields.append('status')

        instance.save(update_fields=list(set(update_fields)))
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_new_password = serializers.CharField(required=True, min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({'confirm_new_password': 'New passwords do not match.'})
        return attrs


class BuyerAddressSerializer(serializers.ModelSerializer):
    """Buyer shipping addresses with structured location support."""

    location_name = serializers.CharField(source='location.name', read_only=True)
    location_type = serializers.CharField(source='location.location_type', read_only=True)
    full_location = serializers.SerializerMethodField()

    class Meta:
        model = BuyerAddress
        fields = [
            'id', 'label', 'street_address', 'location', 'location_name', 'location_type',
            'full_location', 'town_city', 'province', 'postal_code', 'delivery_notes',
            'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'location_name', 'location_type', 'full_location']

    def get_full_location(self, obj):
        if obj.location:
            return obj.location.get_full_address()
        return ''

    @staticmethod
    def _resolve_city_province(location):
        city = ''
        province = ''
        current = location

        while current:
            if current.location_type == 'CITY' and not city:
                city = current.name
            if current.location_type == 'PROVINCE' and not province:
                province = current.name
            current = current.parent

        return city, province

    def validate_location(self, value):
        if value and not value.is_active:
            raise serializers.ValidationError('Selected location is inactive.')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)

        location = attrs.get('location') or getattr(self.instance, 'location', None)
        if location:
            city, province = self._resolve_city_province(location)
            attrs['town_city'] = city or attrs.get('town_city', '')
            attrs['province'] = province or attrs.get('province', '')

        if not (attrs.get('town_city') or getattr(self.instance, 'town_city', '')):
            raise serializers.ValidationError({'town_city': 'Town/City is required.'})

        if not (attrs.get('province') or getattr(self.instance, 'province', '')):
            raise serializers.ValidationError({'province': 'Province is required.'})

        return attrs


class VerificationRequestSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=['PHONE', 'EMAIL'])


class VerificationConfirmSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=['PHONE', 'EMAIL'])
    code = serializers.CharField(min_length=6, max_length=6)
