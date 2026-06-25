# Optimistic — Codebase Site Map

This file documents the project's structure, pages, API surface, apps, models, roles, capabilities, and important restrictions/security rules. Use this as a quick reference for engineering, QA, and reviewers performing cleanup work.

---

## Summary

- Project: Optimistic — multi-seller marketplace (Django + vanilla HTML/CSS/JS)
- Primary goals: escrow-protected commerce, KYC-led onboarding, role-based workflows for Buyers, Sellers, Couriers, Admins
- Canonical design tokens and guidelines: `DESIGN.md`

---

## Roles (business-facing)

- Buyer — browse, add to cart, checkout, request refunds, leave reviews
- Seller — create store, list products (draft -> publish), manage orders, request payouts
- Courier — accept and execute deliveries, update transit/ delivery status
- Admin — verify sellers/couriers, resolve disputes, manage escrow, audit, suspend users

---

## High-level Capabilities & Restrictions

- Escrow: payments are held until delivery confirmation; only Admins may manually release/freeze escrow (`CanManageEscrow`).
- KYC: Sellers and Couriers must be verified by Admin before being allowed trust-sensitive actions (publish products, accept deliveries). See `IsVerifiedSeller`, `IsVerifiedCourier` in `apps/common/permissions.py`.
- Audit logs: Append-only `AuditLog` records exist to track admin actions. They cannot be modified or deleted (see `apps/common/models.py`).
- Ownership: Object-level `IsOwnerOrReadOnly` enforces that resource owners can edit while others have read-only access.

---

## Apps (major folders) — responsibilities & primary models

- `apps/accounts/`
  - Responsibilities: User model, authentication, phone/SMS verification, addresses, payment methods, user middleware
  - Key files: `apps/accounts/models.py`, `apps/accounts/views.py`, `apps/accounts/serializers.py`, `apps/accounts/tests.py`
  - Core models: `User`, `BuyerAddress`, `PaymentMethod`

- `apps/sellers/`
  - Responsibilities: Seller profiles, KYC, store metadata, seller dashboard
  - Key files: `apps/sellers/models.py`, `apps/sellers/serializers.py`, `apps/sellers/views.py`, `apps/sellers/dashboard.py`
  - Core models: `Seller`, `SellerVerification` (verification status, profile data)

- `apps/products/`
  - Responsibilities: Categories, product catalog, images, product moderation
  - Key files: `apps/products/models.py`, `apps/products/serializers.py`, `apps/products/views.py`, `apps/products/admin_views.py`
  - Core models: `Category`, `Product`, `ProductImage`

- `apps/orders/`
  - Responsibilities: Order lifecycle, escrow integration, order items
  - Key files: `apps/orders/models.py`, `apps/orders/serializers.py`, `apps/orders/views.py`
  - Core models: `Order`, `OrderItem`, order-status workflow (PENDING → PAID → PROCESSING → SHIPPED → DELIVERED)

- `apps/logistics/` (may be present under `apps/` as `logistics/`)
  - Responsibilities: Delivery zones, courier assignments, delivery tracking
  - Core models: `Delivery`, `DeliveryPartner` (courier profile)

- `apps/finances/`
  - Responsibilities: Transactions, payouts, seller earnings, reconciliation
  - Core models: `Transaction`, `Payout`

- `apps/disputes/`
  - Responsibilities: Dispute workflow, admin arbitration
  - Core models: `Dispute`

- `apps/reviews/`
  - Responsibilities: Product and seller reviews, rating aggregation
  - Core models: `Review`

- `apps/common/`
  - Responsibilities: Shared utilities, API helpers, validators, permissions, audit logs
  - Key files: `apps/common/permissions.py`, `apps/common/models.py`, `apps/common/api.py`, `apps/common/utils.py`

- `apps/rfq/` — request for quotes (B2B flows)
- `apps/tasks/` — background tasks (async_tasks)

Note: See each app folder for migrations, admin, and management commands.

---

## API Surface (summary)

The API follows REST endpoints under `/api/` (see `config/urls.py` and app `urls.py` files). High-level endpoints:

- Authentication / Accounts
  - `POST /api/accounts/register/` — register
  - `POST /api/accounts/login/` — JWT login
  - `POST /api/accounts/verify-phone/` — SMS verification
  - `GET/PATCH /api/accounts/profile/` — profile management

- Products
  - `GET /api/products/` — list products
  - `GET /api/products/{id}/` — detail
  - `POST /api/sellers/products/` — create (Seller)
  - `PATCH /api/sellers/products/{id}/` — update (Seller/Owner)

- Orders
  - `POST /api/orders/` — create order (escrow)
  - `GET /api/orders/` — list user's orders
  - Order status transitions are enforced server-side

- Sellers
  - `POST /api/sellers/register/` — become seller
  - `POST /api/sellers/kyc/submit/` — submit KYC docs
  - `GET /api/sellers/products/` — seller products

- Admin
  - `GET /api/admin/sellers/pending/` — pending verifications
  - `POST /api/admin/sellers/{id}/verify/` — approve seller
  - Escrow & disputes: admin-only endpoints guarded by `CanManageEscrow`, `CanResolveDisputes`

For full endpoint list, see the README