# 🚀 Optimistic — Multi-Seller Marketplace

**A trust-first e-commerce platform built for Zambia**

Optimistic is a full-featured marketplace connecting buyers, sellers, and couriers with escrow protection, role-based access control, and comprehensive KYC verification — all adapted for Zambian payment and logistics realities.

---

## 🌟 Key Features

### 🛡️ **Trust & Security**
- **Escrow Protection** — Buyer funds held until delivery confirmed
- **KYC Verification** — Seller identity verification with government ID
- **Admin Moderation** — Manual approval gates for quality control
- **Role-Based Access Control** — Separate workflows for Buyers, Sellers, Admins, Couriers

### 🏪 **Multi-Seller Marketplace**
- **Unlimited Sellers** — Anyone can register and sell after verification
- **Store Profiles** — Custom branding with profile images and banners
- **Product Management** — Full catalog with images, variants, stock tracking
- **Order Fulfillment** — Self-fulfilled or agent network delivery

### 💳 **Zambian Payment Methods**
- **Mobile Money** — MTN MoMo, Airtel Money, Zamtel Kwacha
- **Flexible Payouts** — Sellers receive earnings via mobile money or bank
- **Saved Payment Methods** — Buyers can save multiple payment options

### 📦 **Complete Order System**
- **Order Lifecycle** — PENDING → PAID → PROCESSING → SHIPPED → DELIVERED
- **Delivery Tracking** — Real-time status updates
- **Dispute Resolution** — Built-in escrow dispute workflow
- **Multiple Addresses** — Buyers can save home, work, rural locations

### 👥 **User Roles**

| Role | Capabilities |
|------|-------------|
| **Buyer** | Browse products, add to cart, checkout with escrow, track orders, leave reviews |
| **Seller** | Manage store profile, list products, process orders, track earnings, handle disputes |
| **Courier** | Accept deliveries, update location, confirm dropoffs, receive payments |
| **Admin** | Verify sellers, moderate products, resolve disputes, view analytics, manage users |

---

## 📁 Project Structure

```
Optimistic/
├── config/                   # Django settings & root URLs
├── apps/
│   ├── accounts/             # Users, authentication, roles, addresses, payments
│   ├── sellers/              # Seller profiles, KYC verification
│   ├── products/             # Product catalog, categories, images
│   ├── orders/               # Order management, escrow, delivery
│   ├── couriers/             # Courier profiles, delivery tracking
│   ├── reviews/              # Product & seller reviews
│   ├── disputes/             # Dispute resolution workflow
│   ├── finances/             # Payments, payouts, transactions
│   ├── logistics/            # Delivery zones, shipping rates
│   ├── notifications/        # SMS & email notifications
│   └── common/               # Shared utilities, permissions, validators
├── frontend/                 # Vanilla JS frontend (38 HTML pages)
│   ├── js/                   # Navigation, role guards, escrow badges
│   ├── css/                  # Responsive styling
│   ├── buyer-dashboard.html
│   ├── seller-dashboard-v2.html
│   └── admin-dashboard-v2.html
├── manage.py
├── requirements.txt
├── README.md
├── TECHNICAL_PROJECT_OVERVIEW.md
├── ROLE_WORKFLOWS_COMPLETE.md
├── KYC_ONBOARDING_SYSTEM.md
├── KYC_MIGRATION_GUIDE.md
└── IMPLEMENTATION_GUIDE.md
```

---

## 🛠️ Tech Stack

- **Backend**: Django 5.0.1 + Django REST Framework 3.14.0
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT with djangorestframework-simplejwt
- **Frontend**: Vanilla JavaScript (no frameworks)
- **Styling**: Custom CSS with mobile-responsive design
- **File Storage**: Local (development) / S3/Cloudinary (production)
- **Payments**: Mobile Money APIs (MTN MoMo, Airtel Money, Zamtel)

---

## 🚀 Quick Start

### 1. Clone & Navigate

```powershell
git clone <repository-url>
cd Optimistic
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
venv\Scripts\activate  # Windows
# OR
source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment

```powershell
# Copy example environment file
Copy-Item .env.example .env

# Edit .env with your settings:
# - SECRET_KEY
# - DATABASE_URL (if using PostgreSQL)
# - SMS API credentials (optional for MVP)
```

### 5. Run Migrations

```powershell
python manage.py migrate
```

### 6. Create Superuser (Admin)

```powershell
python manage.py createsuperuser
# Username: admin
# Email: admin@optimistic.co.zm
# Password: (your secure password)
```

### 7. Start Development Server

```powershell
python manage.py runserver
```

Visit:
- **Frontend**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **API Root**: http://localhost:8000/api/

---

## 📚 Documentation

### Core Documentation

1. **[TECHNICAL_PROJECT_OVERVIEW.md](TECHNICAL_PROJECT_OVERVIEW.md)**  
   Complete architecture overview, database schema, API design

2. **[ROLE_WORKFLOWS_COMPLETE.md](ROLE_WORKFLOWS_COMPLETE.md)**  
   Detailed workflows for Buyers, Sellers, and Admins with page-by-page flows

3. **[KYC_ONBOARDING_SYSTEM.md](KYC_ONBOARDING_SYSTEM.md)**  
   Comprehensive KYC & onboarding flow adapted for Zambia

4. **[KYC_MIGRATION_GUIDE.md](KYC_MIGRATION_GUIDE.md)**  
   Step-by-step guide to implement KYC database changes

5. **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)**  
   Frontend integration guide for role guards and escrow badges

### Key Features Documentation

#### 🔐 KYC & Verification System

**Buyer Onboarding:**
- Name, email, phone, password → SMS verification
- Optional profile picture
- Saved shipping addresses (multiple locations)
- Saved payment methods (mobile money, cards)

**Seller Onboarding:**
- Store setup (name, description, profile + banner images)
- Business info (type, registration, tax PIN)
- Physical address (street, town, province)
- Payout setup (mobile money or bank account)
- Identity verification (government ID upload)
- Admin review and approval

**Admin Dashboard:**
- Seller verification queue
- ID document review interface
- Approve/reject with notes
- User management (suspend/reinstate)
- Dispute resolution
- Platform analytics

#### 🛡️ Escrow Protection

All buyer payments go into escrow until:
1. Seller ships product
2. Courier delivers (or buyer self-confirms)
3. Admin resolves any disputes

**Escrow States:**
- `HELD` → Funds protected, awaiting delivery
- `RELEASED` → Delivered successfully, funds to seller
- `REFUNDED` → Dispute resolved in buyer's favor

#### 🚚 Delivery System

**Delivery Zones:**
- Urban → Standard shipping fee
- Peri-urban → Mid-range fee
- Rural → Higher fee + GPS coordinates support

**Courier Workflow:**
1. Accept delivery assignment
2. Pickup from seller
3. Transit (live location tracking)
4. Delivery attempt
5. Confirm dropoff (or failure)
6. Receive payment

---

## 🗄️ Database Models

### Core Models

```python
# User Management
User (accounts)           # Base user with role (BUYER/SELLER/COURIER/ADMIN)
BuyerAddress (accounts)   # Saved shipping addresses
PaymentMethod (accounts)  # Saved payment methods

# Seller Marketplace
Seller (sellers)                # Store profiles
SellerVerification (sellers)    # KYC documents (ID uploads)

# Products
Product (products)        # Product catalog
ProductImage (products)   # Multiple images per product
Category (products)       # Product categories

# Orders
Order (orders)            # Order records with escrow
OrderItem (orders)        # Line items
Delivery (logistics)      # Delivery tracking

# Trust System
Review (reviews)          # Product & seller reviews
Dispute (disputes)        # Dispute resolution

# Finances
Transaction (finances)    # Payment records
Payout (finances)         # Seller earnings
```

---

## 🔌 API Endpoints

### Authentication

```
POST   /api/accounts/register/         # User registration
POST   /api/accounts/login/            # JWT login
POST   /api/accounts/verify-phone/     # SMS verification
GET    /api/accounts/profile/          # User profile
PATCH  /api/accounts/profile/          # Update profile
```

### Buyer Endpoints

```
GET    /api/products/                  # List products
GET    /api/products/{id}/             # Product detail
POST   /api/orders/                    # Create order (with escrow)
GET    /api/orders/                    # My orders
GET    /api/accounts/addresses/        # Saved addresses
POST   /api/accounts/addresses/        # Add address
GET    /api/accounts/payment-methods/  # Saved payments
POST   /api/accounts/payment-methods/  # Add payment
```

### Seller Endpoints

```
POST   /api/sellers/register/          # Become seller
PATCH  /api/sellers/profile/           # Update store
POST   /api/sellers/kyc/submit/        # Submit KYC docs
GET    /api/sellers/products/          # My products
POST   /api/sellers/products/          # Create product
PATCH  /api/sellers/products/{id}/     # Update product
GET    /api/sellers/orders/            # Orders to fulfill
GET    /api/sellers/earnings/          # Earnings dashboard
```

### Admin Endpoints

```
GET    /api/admin/sellers/pending/     # Pending verifications
POST   /api/admin/sellers/{id}/verify/ # Approve seller
POST   /api/admin/sellers/{id}/reject/ # Reject seller
GET    /api/admin/disputes/            # Active disputes
POST   /api/admin/disputes/{id}/resolve/ # Resolve dispute
GET    /api/admin/analytics/           # Platform metrics
```

---

## 🎨 Frontend Structure

### Pages by Role

**Public Pages (No Login Required):**
- [index.html](frontend/index.html) — Homepage
- [products.html](frontend/products.html) — Product catalog
- [product-detail.html](frontend/product-detail.html) — Product page
- [about.html](frontend/about.html) — About Optimistic
- [contact.html](frontend/contact.html) — Contact form
- [login.html](frontend/login.html) — Login
- [register.html](frontend/register.html) — Registration

**Buyer Pages:**
- [buyer-dashboard.html](frontend/buyer-dashboard.html) — Order history, saved items
- [cart.html](frontend/cart.html) — Shopping cart
- [checkout.html](frontend/checkout.html) — Checkout with escrow badges
- [orders.html](frontend/orders.html) — Order tracking
- [order-detail.html](frontend/order-detail.html) — Single order details
- [wishlist.html](frontend/wishlist.html) — Saved products

**Seller Pages:**
- [seller-dashboard-v2.html](frontend/seller-dashboard-v2.html) — Sales overview
- [seller-products-v2.html](frontend/seller-products-v2.html) — Product management
- [seller-orders-v2.html](frontend/seller-orders-v2.html) — Order fulfillment
- [seller-earnings-v2.html](frontend/seller-earnings-v2.html) — Revenue tracking
- [seller-store-v2.html](frontend/seller-store-v2.html) — Store settings
- [seller-disputes-v2.html](frontend/seller-disputes-v2.html) — Dispute handling
- [add-product.html](frontend/add-product.html) — Create/edit product

**Admin Pages:**
- [admin-dashboard-v2.html](frontend/admin-dashboard-v2.html) — Platform health
- [admin-users-v2.html](frontend/admin-users-v2.html) — User management
- [admin-products-v2.html](frontend/admin-products-v2.html) — Product moderation
- [admin-orders-v2.html](frontend/admin-orders-v2.html) — Order oversight
- [admin-disputes-v2.html](frontend/admin-disputes-v2.html) — Dispute resolution
- [admin-reports-v2.html](frontend/admin-reports-v2.html) — Analytics
- [admin-finances-v2.html](frontend/admin-finances-v2.html) — Financial reports
- [admin-settings-v2.html](frontend/admin-settings-v2.html) — Platform settings

### JavaScript Components

```javascript
// Core Components (frontend/js/)
navigation.js           // Role-adaptive navigation menus
roleGuard.js            // Page access control (redirect wrong roles)
escrowBadge.js          // Trust badges for buyer pages
api.js                  // API wrapper with JWT handling
auth.js                 // Login/logout/token management
cart.js                 // Shopping cart functionality
```

---

## 🧪 Testing

### Run Tests

```powershell
# All tests
python manage.py test

# Specific app
python manage.py test apps.accounts
python manage.py test apps.sellers

# With coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### Create Test Data

```powershell
python manage.py shell
```

```python
from apps.accounts.models import User
from apps.sellers.models import Seller

# Create test buyer
buyer = User.objects.create_user(
    username='buyer1',
    email='buyer@test.com',
    password='testpass123',
    role='BUYER',
    phone_number='+260977123456',
    phone_verified=True
)

# Create test seller
seller_user = User.objects.create_user(
    username='seller1',
    email='seller@test.com',
    password='testpass123',
    role='SELLER',
    phone_number='+260966123456',
    phone_verified=True
)

seller = Seller.objects.create(
    user=seller_user,
    store_name='Test Store',
    description='A test store',
    phone='+260966123456',
    physical_address='Plot 123, Test Area',
    town_city='Lusaka',
    province='Lusaka Province',
    payout_method='MOBILE_MONEY',
    payout_provider='MTN_MOMO',
    payout_account_name='Test Seller',
    payout_account_number='0966123456',
    verified=True,
    verification_status='VERIFIED'
)
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG = False` in settings
- [ ] Configure PostgreSQL database
- [ ] Set strong `SECRET_KEY`
- [ ] Configure S3/Cloudinary for media files
- [ ] Set up SMS gateway (Twilio, Africa's Talking)
- [ ] Configure mobile money APIs (MTN MoMo, Airtel Money)
- [ ] Set up SSL certificate (HTTPS)
- [ ] Configure email backend (SendGrid, Mailgun)
- [ ] Set up monitoring (Sentry, DataDog)
- [ ] Configure CORS for frontend domain
- [ ] Run `collectstatic` for static files
- [ ] Set up backup schedule for database

### Environment Variables (.env)

```bash
# Django
SECRET_KEY=your-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=optimistic.co.zm,www.optimistic.co.zm

# Database
DATABASE_URL=postgresql://user:pass@localhost/optimistic_db

# File Storage
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=optimistic-media

# SMS/Email
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
SENDGRID_API_KEY=your-sendgrid-key

# Payment APIs
MTN_MOMO_API_KEY=your-mtn-key
AIRTEL_MONEY_API_KEY=your-airtel-key
```

---

## 🤝 Contributing

Optimistic is a private project. For questions or collaboration inquiries, contact the development team.

---

## 📄 License

Proprietary. All rights reserved.

---

## 🆘 Support

For technical issues or questions:
1. Check [TECHNICAL_PROJECT_OVERVIEW.md](TECHNICAL_PROJECT_OVERVIEW.md)
2. Review role-specific docs in [ROLE_WORKFLOWS_COMPLETE.md](ROLE_WORKFLOWS_COMPLETE.md)
3. Consult KYC implementation in [KYC_ONBOARDING_SYSTEM.md](KYC_ONBOARDING_SYSTEM.md)

---

**Built with ❤️ for Zambia** 🇿🇲

**Last Updated**: February 27, 2026  
**Version**: 1.0.0  
**Status**: Production Ready (Pending KYC Migration)
