# 🔐 Optimistic KYC & Onboarding System

**Zambia-Adapted Marketplace Trust & Security Framework**

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Design Philosophy](#design-philosophy)
3. [Buyer Onboarding Flow](#buyer-onboarding-flow)
4. [Seller Onboarding Flow](#seller-onboarding-flow)
5. [Admin Workflow](#admin-workflow)
6. [Database Schema](#database-schema)
7. [Implementation Phases](#implementation-phases)
8. [Security & Compliance](#security--compliance)
9. [API Endpoints](#api-endpoints)
10. [Frontend Integration](#frontend-integration)

---

## 🎯 System Overview

Optimistic implements a **tiered verification system** that balances:
- **Low friction** for quick onboarding  
- **Progressive trust** building as users engage  
- **Escrow protection** without heavy upfront KYC  
- **Local adaptation** for Zambian payment & logistics realities

### Core Principles

1. **Start Minimal** → Collect only what's needed to transact
2. **Build Trust Gradually** → Increase verification as stakes increase
3. **Escrow = Safety Net** → Protects both parties even with light KYC
4. **Mobile-First** → SMS verification, mobile money, agent networks
5. **Admin Oversight** → Manual verification gates for quality control

---

## 🧍 Buyer Onboarding Flow

**Goal:** Enable shopping in < 2 minutes while collecting essentials for delivery and payment.

### Phase 1: MVP (Immediate Implementation)

| Step | Information Collected | Required? | Purpose |
|------|----------------------|-----------|---------|
| **1. Account Creation** | Full Name, Email, Phone, Password | ✅ | Identity + Login |
| **2. Phone Verification** | SMS Code | ✅ | Anti-fraud, trust signal |
| **3. Profile Setup** | Profile Picture | ⚪ Optional | Social features, trust |
| **4. First Purchase** | Shipping Address (Street, Town, Province) | ✅ | Delivery coordination |
| | Delivery Notes (GPS, landmarks) | ⚪ Optional | Rural delivery accuracy |
| | Payment Method (Mobile Money: MTN/Airtel/Zamtel) | ✅ | Transaction processing |

### Phase 2: Enhanced Features

- **Saved Addresses** → Multiple delivery locations for convenience
- **Payment Methods** → Multiple mobile money accounts/cards
- **Loyalty Program** → Points/rewards for repeat purchases
- **Advanced KYC** → ID upload for high-value purchases (>ZMW 5,000)

### Buyer Data Model

```python
User:
  - full_name (first_name + last_name from AbstractUser)
  - email ✅
  - phone_number (new field)
  - profile_picture (optional)
  - phone_verified (boolean)
  - created_at, last_login

BuyerAddress (separate model):
  - user (FK to User)
  - street_address
  - town_city
  - province
  - postal_code (optional)
  - delivery_notes (GPS, landmarks)
  - is_default (boolean)
  - label ('Home', 'Work', etc.)

PaymentMethod (separate model):
  - user (FK to User)
  - method_type ('MOBILE_MONEY', 'CARD', 'WALLET')
  - provider ('MTN_MOMO', 'AIRTEL_MONEY', 'ZAMTEL')
  - account_identifier (tokenized/encrypted)
  - is_default (boolean)
  - verified (boolean)
```

---

## 🏪 Seller Onboarding Flow

**Goal:** Verify identity, enable payouts, allow product listings with admin oversight.

### Phase 1: MVP (Immediate Implementation)

| Step | Information Collected | Required? | Purpose |
|------|----------------------|-----------|---------|
| **1. Account Creation** | Full Name, Email, Phone, Password | ✅ | Basic access |
| **2. Business Info** | Business Name, Business Type | ⚪ | Optional for MSMEs |
| | Store Name | ✅ | Public-facing identity |
| | Store Description | ✅ | Trust-building |
| | Store Profile Image | ✅ | Brand identity |
| | Store Cover/Banner Image | ✅ | Professional appearance |
| **3. Identity Verification** | Government ID / Passport (upload) | ✅ | KYC compliance, fraud prevention |
| | Full Legal Name | ✅ | Must match ID |
| | Physical Business Address | ✅ | Legal compliance |
| **4. Payout Setup** | Bank Account OR Mobile Money | ✅ | Seller payouts |
| | Account Name | ✅ | Verification |
| | Account Number | ✅ | Transfer processing |
| **5. Product Listing** | Product Name, Description, Price, Images, Stock, Category | ✅ | Start selling |
| **6. Shipping Options** | Self-fulfilled OR Agent Network | ✅ | Logistics setup |

### Phase 2: Enhanced Features

- **Business Registration Number** → For formal businesses (optional initially)
- **Tax Identification (TPIN)** → VAT compliance for scalers
- **Brand Certificates** → Authorization for branded/restricted goods
- **Performance Dashboard** → Real-time analytics
- **Tier System** → Bronze/Silver/Gold based on performance

### Seller Verification States

```
PENDING → ID_SUBMITTED → ADMIN_REVIEW → VERIFIED → ACTIVE
                ↓
            REJECTED (with reason)
```

### Seller Data Model

```python
Seller (extends existing model):
  - user (OneToOne to User)
  - store_name ✅
  - store_description ✅
  - profile_image ✅
  - banner_image ✅
  - phone ✅
  - verified ✅
  
  # NEW FIELDS (KYC)
  - business_type ('SOLE_TRADER', 'PARTNERSHIP', 'COMPANY')
  - business_name (optional)
  - business_registration_number (optional)
  - tax_pin (optional)
  
  # Address
  - physical_address (street)
  - town_city
  - province
  
  # Payout
  - payout_method ('BANK', 'MOBILE_MONEY')
  - payout_provider ('MTN_MOMO', 'AIRTEL_MONEY', 'ZAMTEL', 'BANK')
  - payout_account_name
  - payout_account_number (encrypted)
  
  # Verification
  - verification_status ('PENDING', 'SUBMITTED', 'UNDER_REVIEW', 'VERIFIED', 'REJECTED')
  - verification_notes (admin notes)
  - verified_at (timestamp)
  - verified_by (FK to User - admin)

SellerVerification (separate model for KYC docs):
  - seller (FK to Seller)
  - government_id_type ('NRC', 'PASSPORT', 'DRIVERS_LICENSE')
  - government_id_number (encrypted)
  - government_id_front (image upload)
  - government_id_back (image upload)
  - selfie_with_id (optional - advanced fraud prevention)
  - submitted_at
  - reviewed_at
  - reviewed_by (FK to User - admin)
  - status ('PENDING', 'APPROVED', 'REJECTED')
  - rejection_reason
```

---

## 👨‍💼 Admin Workflow

**Goal:** Monitor, moderate, verify, resolve disputes, maintain platform health.

### Dashboard Overview

```
┌─────────────────────────────────────────┐
│  Platform Health Snapshot               │
├─────────────────────────────────────────┤
│  Active Buyers: 1,234                   │
│  Active Sellers: 156                    │
│  Pending Verifications: 8               │
│  Active Orders: 45                      │
│  Open Disputes: 3                       │
│  Escrow Balance: ZMW 125,340            │
└─────────────────────────────────────────┘
```

### Admin Tasks

| Task | Description | Priority |
|------|-------------|----------|
| **User Management** | View/suspend/terminate users | High |
| **Seller Verification** | Review ID uploads, approve/reject | Critical |
| **Product Moderation** | Flag/remove prohibited items | High |
| **Dispute Resolution** | Escrow release/refund decisions | Critical |
| **Analytics** | Revenue, seller performance, errors | Medium |
| **System Logs** | Audit trail for compliance | Medium |

### Seller Verification Process

1. Seller submits ID documents
2. Admin receives notification
3. Admin reviews:
   - ID authenticity (visual inspection)
   - Name match (Legal Name = ID Name)
   - Address validity (Google Maps check)
   - Business info consistency
4. **APPROVE** → Seller.verified = True → Can publish products
5. **REJECT** → Seller notified with reason → Can resubmit

---

## 🗄️ Database Schema

### New Models to Create

```python
# apps/accounts/models.py (additions to existing User model)

class User(AbstractUser):
    # ... existing fields ...
    
    # NEW: Phone verification
    phone_number = models.CharField(max_length=20, unique=True, help_text="Primary phone for SMS verification")
    phone_verified = models.BooleanField(default=False)
    phone_verified_at = models.DateTimeField(null=True, blank=True)


# apps/accounts/models.py (new models)

class BuyerAddress(models.Model):
    """Saved shipping addresses for buyers."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, default='Home', help_text="Address nickname")
    street_address = models.TextField(help_text="Street/building/plot number")
    town_city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    delivery_notes = models.TextField(blank=True, help_text="GPS coordinates, landmarks, gate instructions")
    is_default = models.BooleanField(default=False, help_text="Use this address by default")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Buyer Addresses'
        ordering = ['-is_default', '-created_at']


class PaymentMethod(models.Model):
    """Saved payment methods for buyers."""
    METHOD_CHOICES = (
        ('MOBILE_MONEY', 'Mobile Money'),
        ('CARD', 'Debit/Credit Card'),
        ('WALLET', 'Optimistic Wallet'),
    )
    
    PROVIDER_CHOICES = (
        ('MTN_MOMO', 'MTN Mobile Money'),
        ('AIRTEL_MONEY', 'Airtel Money'),
        ('ZAMTEL', 'Zamtel Kwacha'),
        ('VISA', 'Visa'),
        ('MASTERCARD', 'Mastercard'),
        ('OPTIMISTIC', 'Optimistic Wallet'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=METHOD_CHOICES)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    account_identifier = models.CharField(max_length=255, help_text="Encrypted phone/card token")
    account_name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']


# apps/sellers/models.py (additions to existing Seller model)

class Seller(models.Model):
    # ... existing fields ...
    
    # NEW: Business Information
    BUSINESS_TYPE_CHOICES = (
        ('SOLE_TRADER', 'Sole Trader'),
        ('PARTNERSHIP', 'Partnership'),
        ('COMPANY', 'Registered Company'),
    )
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES, blank=True)
    business_name = models.CharField(max_length=200, blank=True, help_text="Legal business name")
    business_registration_number = models.CharField(max_length=100, blank=True, help_text="PACRA/BDS number")
    tax_pin = models.CharField(max_length=50, blank=True, help_text="Tax Identification Number")
    
    # NEW: Physical Address
    physical_address = models.TextField(help_text="Business street address")
    town_city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    
    # NEW: Payout Information
    PAYOUT_METHOD_CHOICES = (
        ('BANK', 'Bank Account'),
        ('MOBILE_MONEY', 'Mobile Money'),
    )
    
    PAYOUT_PROVIDER_CHOICES = (
        ('MTN_MOMO', 'MTN Mobile Money'),
        ('AIRTEL_MONEY', 'Airtel Money'),
        ('ZAMTEL', 'Zamtel Kwacha'),
        ('BANK', 'Bank Transfer'),
    )
    
    payout_method = models.CharField(max_length=20, choices=PAYOUT_METHOD_CHOICES)
    payout_provider = models.CharField(max_length=20, choices=PAYOUT_PROVIDER_CHOICES)
    payout_account_name = models.CharField(max_length=200, help_text="Account holder name")
    payout_account_number = models.CharField(max_length=100, help_text="Account/phone number")
    
    # NEW: Verification Status (more granular than just verified=True/False)
    VERIFICATION_STATUS_CHOICES = (
        ('PENDING', 'Pending - Not Submitted'),
        ('SUBMITTED', 'Documents Submitted'),
        ('UNDER_REVIEW', 'Under Admin Review'),
        ('VERIFIED', 'Verified and Active'),
        ('REJECTED', 'Rejected'),
    )
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='PENDING')
    verification_notes = models.TextField(blank=True, help_text="Admin notes on verification")
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_sellers')


# apps/sellers/models.py (new model)

class SellerVerification(models.Model):
    """KYC documents for seller verification."""
    
    ID_TYPE_CHOICES = (
        ('NRC', 'National Registration Card'),
        ('PASSPORT', 'Passport'),
        ('DRIVERS_LICENSE', 'Driver\'s License'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    seller = models.OneToOneField(Seller, on_delete=models.CASCADE, related_name='kyc_documents')
    
    # ID Information
    government_id_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES)
    government_id_number = models.CharField(max_length=50, help_text="Encrypted ID number")
    government_id_front = models.ImageField(upload_to='kyc/ids/', help_text="Front of ID")
    government_id_back = models.ImageField(upload_to='kyc/ids/', help_text="Back of ID")
    selfie_with_id = models.ImageField(upload_to='kyc/selfies/', null=True, blank=True, help_text="Selfie holding ID (optional)")
    
    # Review Information
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_kyc')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Seller Verification Documents'
        verbose_name_plural = 'Seller Verification Documents'
```

---

## 🚀 Implementation Phases

### Phase 1: MVP (Weeks 1-2)

**Buyer Side:**
- ✅ Profile picture (optional) - Already exists
- ➕ Phone number field + SMS verification
- ➕ BuyerAddress model for saved addresses
- ➕ PaymentMethod model for mobile money
- ➕ Registration flow with minimal fields

**Seller Side:**
- ✅ Store profile + banner images - Already exists
- ➕ Business address fields (street, town, province)
- ➕ Payout account fields (method, provider, account)
- ➕ SellerVerification model for ID uploads
- ➕ Admin approval workflow

**Admin Side:**
- ➕ Seller verification dashboard
- ➕ ID document review interface
- ➕ Approve/reject actions with notes

### Phase 2: Enhanced Features (Weeks 3-4)

**Buyer Side:**
- Multiple saved addresses
- Multiple payment methods
- Address book management UI
- High-value purchase KYC (>ZMW 5,000)

**Seller Side:**
- Business registration number field
- Tax PIN field
- Performance tier system (Bronze/Silver/Gold)
- Analytics dashboard expansion

**Admin Side:**
- Bulk verification actions
- KYC audit trail
- Compliance reports
- Seller performance scoring

---

## 🔒 Security & Compliance

### Data Protection

1. **Sensitive Field Encryption**
   - Government ID numbers
   - Payment account numbers
   - KYC documents stored with restricted access

2. **Access Control**
   - Only admins can view full KYC documents
   - Sellers see only their own data
   - Buyers see only their own data

3. **Audit Trail**
   - All verification actions logged
   - Admin actions recorded with timestamp + user
   - Immutable history for compliance

### Zambian Compliance

1. **Data Protection Act (2021)**
   - User consent for data collection
   - Right to access personal data
   - Right to deletion (after dispute resolution)

2. **KYC Requirements (Bank of Zambia)**
   - Government ID verification for sellers
   - Business registration for formal entities
   - Tax compliance for high-volume sellers

3. **Consumer Protection**
   - Escrow holds until delivery confirmed
   - Dispute resolution within 14 days
   - Refund processing within 7 days

---

## 🔌 API Endpoints

### Buyer Endpoints

```
POST   /api/accounts/register/buyer/          # Create buyer account
POST   /api/accounts/verify-phone/            # SMS verification
GET    /api/accounts/profile/                 # Get user profile
PATCH  /api/accounts/profile/                 # Update profile (incl. photo)

GET    /api/accounts/addresses/               # List saved addresses
POST   /api/accounts/addresses/               # Add new address
PATCH  /api/accounts/addresses/{id}/          # Update address
DELETE /api/accounts/addresses/{id}/          # Delete address
POST   /api/accounts/addresses/{id}/default/  # Set as default

GET    /api/accounts/payment-methods/         # List payment methods
POST   /api/accounts/payment-methods/         # Add payment method
PATCH  /api/accounts/payment-methods/{id}/    # Update payment method
DELETE /api/accounts/payment-methods/{id}/    # Delete payment method
POST   /api/accounts/payment-methods/{id}/verify/  # Verify via SMS
```

### Seller Endpoints

```
POST   /api/sellers/register/                 # Create seller account
PATCH  /api/sellers/profile/                  # Update store info + images
POST   /api/sellers/kyc/submit/               # Submit KYC documents
GET    /api/sellers/kyc/status/               # Check verification status

PATCH  /api/sellers/business-info/            # Update business details
PATCH  /api/sellers/payout-info/              # Update payout account
```

### Admin Endpoints

```
GET    /api/admin/sellers/pending/            # List sellers awaiting verification
GET    /api/admin/sellers/{id}/kyc/           # View KYC documents
POST   /api/admin/sellers/{id}/verify/        # Approve seller
POST   /api/admin/sellers/{id}/reject/        # Reject seller (with reason)

GET    /api/admin/users/                      # List all users
POST   /api/admin/users/{id}/suspend/         # Suspend user
POST   /api/admin/users/{id}/reinstate/       # Reinstate user
```

---

## 🎨 Frontend Integration

### Buyer Registration Flow

**Page: register.html**

```javascript
// Step 1: Basic Info
<input type="text" name="first_name" placeholder="First Name" required>
<input type="text" name="last_name" placeholder="Last Name" required>
<input type="email" name="email" placeholder="Email" required>
<input type="tel" name="phone_number" placeholder="Phone (e.g., +260 97 123 4567)" required>
<input type="password" name="password" required>

// Step 2: Phone Verification
POST /api/accounts/verify-phone/ → SMS code sent
<input type="text" name="verification_code" placeholder="Enter 6-digit code">

// Step 3: Profile Picture (Optional)
<input type="file" name="profile_picture" accept="image/*">
<button type="button">Skip for now</button>

// Step 4: First Purchase triggers address + payment setup
```

### Seller Registration Flow

**Page: seller-register.html**

```javascript
// Tab 1: Account Creation
<input type="text" name="first_name" required>
<input type="text" name="last_name" required>
<input type="email" name="email" required>
<input type="tel" name="phone_number" required>

// Tab 2: Store Setup
<input type="text" name="store_name" placeholder="Your Store Name" required>
<textarea name="description" placeholder="Tell buyers about your business" required></textarea>
<input type="file" name="profile_image" accept="image/*" required>
<input type="file" name="banner_image" accept="image/*" required>

// Tab 3: Business Info (Optional MVP)
<select name="business_type">
  <option value="SOLE_TRADER">Sole Trader</option>
  <option value="COMPANY">Registered Company</option>
</select>
<input type="text" name="business_name" placeholder="Legal Business Name (Optional)">

// Tab 4: Physical Address
<textarea name="physical_address" placeholder="Street/Plot Number" required></textarea>
<input type="text" name="town_city" required>
<select name="province" required>
  <option>Lusaka</option>
  <option>Copperbelt</option>
  <!-- All 10 provinces -->
</select>

// Tab 5: Payout Setup
<select name="payout_method" required>
  <option value="MOBILE_MONEY">Mobile Money</option>
  <option value="BANK">Bank Account</option>
</select>
<select name="payout_provider" required>
  <option value="MTN_MOMO">MTN Mobile Money</option>
  <option value="AIRTEL_MONEY">Airtel Money</option>
  <option value="ZAMTEL">Zamtel Kwacha</option>
</select>
<input type="text" name="payout_account_name" required>
<input type="text" name="payout_account_number" placeholder="Phone or Account Number" required>

// Tab 6: Identity Verification
<select name="government_id_type" required>
  <option value="NRC">National Registration Card</option>
  <option value="PASSPORT">Passport</option>
</select>
<input type="text" name="government_id_number" required>
<input type="file" name="id_front" accept="image/*" required>
<input type="file" name="id_back" accept="image/*" required>

<button type="submit">Submit for Verification</button>
```

### Admin Verification Interface

**Page: admin-sellers-v2.html**

```javascript
// Pending Sellers Table
┌─────────────────────────────────────────────────────────────┐
│ Store Name    │ Submitted │ Business Type │ Status   │ Action │
├─────────────────────────────────────────────────────────────┤
│ Joe's Phones  │ 2h ago    │ Sole Trader   │ PENDING  │ [Review] │
│ TechMart ZM   │ 1d ago    │ Company       │ PENDING  │ [Review] │
└─────────────────────────────────────────────────────────────┘

// Verification Modal (on clicking [Review])
┌────────────────────────────────────────────┐
│  Seller Verification: Joe's Phones         │
├────────────────────────────────────────────┤
│  Store Name: Joe's Phones                  │
│  Legal Name: Joseph Banda                  │
│  Phone: +260 97 123 4567                   │
│  Address: Plot 123, Longacres, Lusaka      │
│                                            │
│  ID Type: NRC                              │
│  ID Number: 123456/78/9                    │
│  [View ID Front] [View ID Back]            │
│                                            │
│  Payout: MTN MoMo - 0977123456             │
│                                            │
│  ✅ ID matches legal name                  │
│  ✅ Clear photo quality                    │
│  ✅ Address seems valid                    │
│                                            │
│  Admin Notes:                              │
│  <textarea placeholder="Notes..."></textarea> │
│                                            │
│  [✅ Approve] [❌ Reject]                   │
└────────────────────────────────────────────┘
```

---

## 📊 Success Metrics

### Buyer Metrics

- Registration completion rate: Target >85%
- Phone verification rate: Target >95%
- Profile photo upload rate: Target >30% (optional)
- Saved addresses: Avg 1.8 per active buyer

### Seller Metrics

- Registration to submission: Target <24 hours
- Verification approval rate: Target >90%
- Time to first product listing: Target <48 hours
- Store profile completion: Target 100% (required)

### Admin Metrics

- Verification turnaround time: Target <24 hours
- Dispute resolution time: Target <3 days
- False positive rejection rate: Target <5%

---

## 🎯 Next Steps

### Immediate Actions (Week 1)

1. **Backend Development**
   - [ ] Add phone_number, phone_verified fields to User model
   - [ ] Create BuyerAddress model
   - [ ] Create PaymentMethod model
   - [ ] Update Seller model with KYC fields
   - [ ] Create SellerVerification model
   - [ ] Run migrations

2. **API Development**
   - [ ] Phone verification endpoint (SMS integration)
   - [ ] Address CRUD endpoints
   - [ ] Payment method CRUD endpoints
   - [ ] Seller KYC submission endpoint
   - [ ] Admin verification endpoints

3. **Frontend Development**
   - [ ] Update register.html with phone field
   - [ ] Create seller-register.html multi-tab form
   - [ ] Create admin verification interface in admin-sellers-v2.html
   - [ ] Add address management to buyer-dashboard.html
   - [ ] Add payment methods to profile.html

4. **Integration**
   - [ ] SMS gateway setup (Zambia provider)
   - [ ] Image upload to S3/Cloudinary
   - [ ] Encryption for sensitive fields
   - [ ] Audit logging

### Future Enhancements (Weeks 2-4)

- [ ] Two-factor authentication (2FA)
- [ ] Seller tier system (Bronze/Silver/Gold)
- [ ] Automatic ID verification (AI/OCR)
- [ ] Video verification for high-risk sellers
- [ ] Buyer loyalty program
- [ ] Tax compliance reporting
- [ ] Bulk seller approval tools
- [ ] KYC renewal (annual review)

---

## 📚 References

- **Django Authentication:** https://docs.djangoproject.com/en/5.0/topics/auth/
- **Image Upload Best Practices:** https://django-storages.readthedocs.io/
- **KYC Regulations (Zambia):** Bank of Zambia Guidelines 2022
- **Mobile Money APIs:** MTN MoMo API, Airtel Money API, Zamtel Kwacha API
- **SMS Gateway (Zambia):** Twilio, Africa's Talking, local providers

---

**Last Updated:** February 27, 2026  
**Version:** 1.0.0  
**Status:** Ready for Implementation
