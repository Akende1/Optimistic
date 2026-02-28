# 🔄 KYC System Migration Guide

**Optimistic Marketplace - Database Model Updates**

---

## 📋 Overview

This guide walks through implementing the KYC (Know Your Customer) system for Optimistic. The changes add comprehensive buyer and seller onboarding with identity verification, address management, and payment methods.

---

## 🗄️ Database Changes Summary

### New Fields in Existing Models

**User Model** (`apps/accounts/models.py`):
- `phone_number` - CharField(20), unique, for SMS verification
- `phone_verified` - BooleanField, default=False
- `phone_verified_at` - DateTimeField, nullable

**Seller Model** (`apps/sellers/models.py`):
- **Business Info**: `business_type`, `business_name`, `business_registration_number`, `tax_pin`
- **Address**: `physical_address`, `town_city`, `province`
- **Payout**: `payout_method`, `payout_provider`, `payout_account_name`, `payout_account_number`
- **Verification**: `verification_status`, `verification_notes`, `verified_at`, `verified_by`

### New Models

1. **BuyerAddress** - Saved shipping addresses for buyers
2. **PaymentMethod** - Saved payment methods (mobile money, cards)
3. **SellerVerification** - KYC documents (ID uploads, verification status)

---

## 🚀 Step-by-Step Migration

### Step 1: Backup Database

```powershell
# Create backup of current database
Copy-Item db.sqlite3 db.sqlite3.backup_$(Get-Date -Format "yyyyMMdd_HHmmss")
```

### Step 2: Verify Model Changes

The model files have already been updated:
- ✅ [apps/accounts/models.py](apps/accounts/models.py)
- ✅ [apps/sellers/models.py](apps/sellers/models.py)

### Step 3: Create Migrations

```powershell
# Navigate to project root
cd C:\Users\rival\Documents\GitHub\Optimistic

# Create migrations for accounts app
python manage.py makemigrations accounts

# Create migrations for sellers app
python manage.py makemigrations sellers

# Review migrations (optional but recommended)
python manage.py sqlmigrate accounts <migration_number>
python manage.py sqlmigrate sellers <migration_number>
```

### Step 4: Apply Migrations

```powershell
# Apply migrations to database
python manage.py migrate accounts
python manage.py migrate sellers

# Verify migration success
python manage.py showmigrations
```

### Step 5: Update Admin Interface

Register new models in admin:

**apps/accounts/admin.py**:
```python
from django.contrib import admin
from .models import User, BuyerAddress, PaymentMethod

# Existing User admin...

@admin.register(BuyerAddress)
class BuyerAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'label', 'town_city', 'province', 'is_default', 'created_at']
    list_filter = ['province', 'is_default']
    search_fields = ['user__username', 'town_city', 'street_address']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'method_type', 'provider', 'is_default', 'verified', 'created_at']
    list_filter = ['method_type', 'provider', 'verified']
    search_fields = ['user__username', 'account_name']
    readonly_fields = ['created_at', 'updated_at']
```

**apps/sellers/admin.py**:
```python
from django.contrib import admin
from .models import Seller, SellerVerification

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'user', 'verification_status', 'verified', 'created_at']
    list_filter = ['verification_status', 'verified', 'business_type', 'province']
    search_fields = ['store_name', 'user__username', 'business_name']
    readonly_fields = ['created_at', 'verified_at', 'verified_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'store_name', 'description', 'phone')
        }),
        ('Images', {
            'fields': ('profile_image', 'banner_image')
        }),
        ('Business Details', {
            'fields': ('business_type', 'business_name', 'business_registration_number', 'tax_pin')
        }),
        ('Address', {
            'fields': ('physical_address', 'town_city', 'province')
        }),
        ('Payout Information', {
            'fields': ('payout_method', 'payout_provider', 'payout_account_name', 'payout_account_number')
        }),
        ('Verification', {
            'fields': ('verification_status', 'verified', 'verification_notes', 'verified_at', 'verified_by')
        }),
    )

@admin.register(SellerVerification)
class SellerVerificationAdmin(admin.ModelAdmin):
    list_display = ['seller', 'government_id_type', 'status', 'submitted_at', 'reviewed_by']
    list_filter = ['status', 'government_id_type']
    search_fields = ['seller__store_name', 'government_id_number']
    readonly_fields = ['submitted_at', 'reviewed_at', 'reviewed_by']
    
    fieldsets = (
        ('Seller', {
            'fields': ('seller',)
        }),
        ('ID Documents', {
            'fields': ('government_id_type', 'government_id_number', 'government_id_front', 'government_id_back', 'selfie_with_id')
        }),
        ('Review', {
            'fields': ('status', 'rejection_reason', 'submitted_at', 'reviewed_at', 'reviewed_by')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of approved verifications for audit trail
        if obj and obj.status == 'APPROVED':
            return False
        return super().has_delete_permission(request, obj)
```

### Step 6: Create Test Data

```powershell
# Open Django shell
python manage.py shell
```

```python
from apps.accounts.models import User, BuyerAddress, PaymentMethod
from apps.sellers.models import Seller, SellerVerification

# Test Buyer with Address
buyer = User.objects.filter(role='BUYER').first()
if buyer:
    # Add phone number
    buyer.phone_number = '+260977123456'
    buyer.phone_verified = True
    buyer.save()
    
    # Add address
    BuyerAddress.objects.create(
        user=buyer,
        label='Home',
        street_address='Plot 123, Longacres',
        town_city='Lusaka',
        province='Lusaka Province',
        delivery_notes='Blue gate, next to Total station',
        is_default=True
    )
    
    # Add payment method
    PaymentMethod.objects.create(
        user=buyer,
        method_type='MOBILE_MONEY',
        provider='MTN_MOMO',
        account_identifier='0977123456',
        account_name='John Banda',
        is_default=True,
        verified=True
    )

# Test Seller with KYC
seller_user = User.objects.filter(role='SELLER').first()
if seller_user and hasattr(seller_user, 'seller'):
    seller = seller_user.seller
    
    # Update seller with KYC info
    seller.business_type = 'SOLE_TRADER'
    seller.physical_address = 'Plot 456, Kabulonga'
    seller.town_city = 'Lusaka'
    seller.province = 'Lusaka Province'
    seller.payout_method = 'MOBILE_MONEY'
    seller.payout_provider = 'MTN_MOMO'
    seller.payout_account_name = 'Joseph Mwamba'
    seller.payout_account_number = '0966123456'
    seller.verification_status = 'PENDING'
    seller.save()
    
    print(f"✅ Seller profile completion: {seller.get_completion_percentage()}%")
```

### Step 7: Update Serializers

**apps/accounts/serializers.py**:
```python
from rest_framework import serializers
from .models import User, BuyerAddress, PaymentMethod

class BuyerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerAddress
        fields = [
            'id', 'label', 'street_address', 'town_city', 'province',
            'postal_code', 'delivery_notes', 'is_default', 'created_at'
        ]
        read_only_fields = ['created_at']

class PaymentMethodSerializer(serializers.ModelSerializer):
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'method_type', 'provider', 'provider_display',
            'account_name', 'is_default', 'verified', 'created_at'
        ]
        read_only_fields = ['created_at', 'verified']
    
    # Exclude sensitive account_identifier from responses
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Mask account identifier (show last 4 digits only)
        if hasattr(instance, 'account_identifier'):
            masked = '*' * (len(instance.account_identifier) - 4) + instance.account_identifier[-4:]
            data['account_identifier_masked'] = masked
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    addresses = BuyerAddressSerializer(many=True, read_only=True)
    payment_methods = PaymentMethodSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'status', 'profile_picture', 'phone_number',
            'phone_verified', 'addresses', 'payment_methods'
        ]
        read_only_fields = ['phone_verified']
```

**apps/sellers/serializers.py**:
```python
from rest_framework import serializers
from .models import Seller, SellerVerification

class SellerVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerVerification
        fields = [
            'id', 'government_id_type', 'government_id_number',
            'government_id_front', 'government_id_back', 'selfie_with_id',
            'status', 'rejection_reason', 'submitted_at'
        ]
        read_only_fields = ['status', 'rejection_reason', 'submitted_at']

class SellerDetailSerializer(serializers.ModelSerializer):
    kyc_documents = SellerVerificationSerializer(read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Seller
        fields = [
            'id', 'store_name', 'description', 'profile_image', 'banner_image',
            'phone', 'business_type', 'business_name', 'physical_address',
            'town_city', 'province', 'payout_method', 'payout_provider',
            'payout_account_name', 'verification_status', 'verified',
            'kyc_documents', 'completion_percentage', 'created_at'
        ]
        read_only_fields = ['verified', 'verification_status', 'created_at']
    
    def get_completion_percentage(self, obj):
        return obj.get_completion_percentage()
```

### Step 8: Create API Views

**apps/accounts/views.py** (add these endpoints):
```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import BuyerAddress, PaymentMethod
from .serializers import BuyerAddressSerializer, PaymentMethodSerializer

class BuyerAddressViewSet(viewsets.ModelViewSet):
    serializer_class = BuyerAddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return BuyerAddress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        address = self.get_object()
        address.is_default = True
        address.save()  # Triggers save() method that unsets other defaults
        return Response({'status': 'default address updated'})

class PaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        payment_method = self.get_object()
        payment_method.is_default = True
        payment_method.save()
        return Response({'status': 'default payment method updated'})
```

### Step 9: Update URLs

**apps/accounts/urls.py**:
```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BuyerAddressViewSet, PaymentMethodViewSet

router = DefaultRouter()
router.register(r'addresses', BuyerAddressViewSet, basename='address')
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')

urlpatterns = [
    # ... existing patterns ...
    path('', include(router.urls)),
]
```

### Step 10: Testing Checklist

- [ ] Migrations applied successfully
- [ ] New models visible in Django Admin
- [ ] Can create BuyerAddress via admin
- [ ] Can create PaymentMethod via admin
- [ ] Can upload SellerVerification documents
- [ ] Seller profile completion percentage calculates correctly
- [ ] Default address/payment logic works (only one default per user)
- [ ] API endpoints return correct data
- [ ] Sensitive fields (account_identifier) are masked in responses

---

## 🔍 Verification Commands

```powershell
# Check migration status
python manage.py showmigrations

# Check model fields in database
python manage.py dbshell
# Then in SQLite:
.schema accounts_user
.schema accounts_buyeraddress
.schema accounts_paymentmethod
.schema sellers_seller
.schema sellers_sellerverification

# Test model access in shell
python manage.py shell
```

```python
from apps.accounts.models import BuyerAddress, PaymentMethod
from apps.sellers.models import SellerVerification

# Verify models are accessible
print(BuyerAddress.objects.count())
print(PaymentMethod.objects.count())
print(SellerVerification.objects.count())
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: Migration Conflicts

**Problem**: Existing migrations conflict with new changes

**Solution**:
```powershell
# Reset migrations (DEVELOPMENT ONLY - do not use in production)
python manage.py migrate accounts zero
python manage.py migrate sellers zero
# Delete migration files
Remove-Item apps/accounts/migrations/0*.py
Remove-Item apps/sellers/migrations/0*.py
# Recreate
python manage.py makemigrations accounts
python manage.py makemigrations sellers
python manage.py migrate
```

### Issue 2: Unique Constraint Violation (phone_number)

**Problem**: Existing users don't have phone numbers, but field is unique

**Solution**: The `phone_number` field is `null=True` and `blank=True`, so existing users are fine. After migration, you can gradually collect phone numbers via profile update.

### Issue 3: Required Fields on Seller Model

**Problem**: Existing sellers don't have new required fields

**Solution**: All new fields have `blank=True` to allow gradual data collection. Sellers can be prompted to complete their profile.

---

## 📊 Post-Migration Data Collection Plan

### Phase 1: Buyers (Immediate)

1. **Add Banner to Buyer Dashboard**:
   ```
   "📍 Complete your profile: Add a shipping address and payment method for faster checkout!"
   ```

2. **Prompt at First Checkout**:
   - If no address → Show address form before payment
   - If no payment method → Show payment method form
   - Save for future use checkbox

### Phase 2: Sellers (Immediate)

1. **Profile Completion Widget**:
   ```
   Your Profile: 65% Complete
   ❌ Add Business Address
   ❌ Add Payout Information
   ❌ Submit KYC Documents
   ```

2. **Block Product Publishing Until Verified**:
   ```python
   # In product creation view
   if not request.user.seller.can_publish_products():
       return Response({
           'error': 'Complete KYC verification to publish products',
           'completion': request.user.seller.get_completion_percentage()
       }, status=403)
   ```

### Phase 3: Admin Verification Queue (Week 1)

1. Create admin dashboard widget showing:
   - Pending verifications count
   - Average verification time
   - Rejection rate

2. Email notifications to admin when new KYC submitted

---

## 🎯 Success Metrics

Track these after migration:

| Metric | Target | Timeframe |
|--------|--------|-----------|
| Buyers with saved addresses | >60% | 2 weeks |
| Buyers with payment methods | >80% | 2 weeks |
| Sellers with complete profiles | >90% | 1 week |
| Sellers with KYC submitted | >75% | 2 weeks |
| KYC approval rate | >85% | Ongoing |
| Average KYC turnaround time | <24 hours | Ongoing |

---

## 📚 Related Documentation

- [KYC_ONBOARDING_SYSTEM.md](KYC_ONBOARDING_SYSTEM.md) - Complete system overview
- [ROLE_WORKFLOWS_COMPLETE.md](ROLE_WORKFLOWS_COMPLETE.md) - Role-based workflows
- [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) - Frontend integration guide

---

**Last Updated**: February 27, 2026  
**Status**: Ready for Migration  
**Estimated Time**: 2-3 hours
