# Optimistic Codebase Guide

Optimistic is a Django/DRF marketplace tailored to Zambian commerce. The static web client lives in `frontend/`; native clients consume `/api/v1/`.

## Repository map

| Path | Responsibility |
|---|---|
| `config/` | Settings, root URLs, WSGI and ASGI |
| `apps/accounts/` | Users, JWT authentication, addresses and verification |
| `apps/sellers/` | Seller profile, KYC and store operations |
| `apps/products/` | Listings, categories, media and physical/reserved inventory |
| `apps/orders/` | Orders, line snapshots, reservations, payments and seller fulfillment |
| `apps/logistics/` | Delivery partners, deliveries, locations and courier payouts |
| `apps/finances/` | Commissions, seller escrow and order financial snapshots |
| `apps/disputes/` | Claims, evidence and financial resolutions |
| `apps/notifications/` | User notifications and lifecycle signals |
| `apps/reviews/` | Verified-purchase reviews |
| `apps/rfq/` | Business quotation requests |
| `apps/common/` | Shared permissions, validation, audit and mobile API composition |
| `apps/tasks/` | Retry-safe scheduled/background task boundaries |
| `frontend/` | Existing web pages, components, scripts and styles |

## Engineering rules

1. Models preserve local invariants; transactional services execute cross-model workflows. Views authenticate, parse, invoke and serialize.
2. Clients never own totals, price snapshots, seller IDs, commissions, escrow amounts, inventory or workflow statuses.
3. `Product.stock` is physical on-hand, `reserved_stock` is held by active checkouts, and `available_stock` is derived.
4. External events are immutable and idempotent. Provider adapters verify raw webhook signatures before invoking commerce services.
5. `OrderFulfillment` scopes work to one order/seller pair; sellers cannot advance another seller's work or the aggregate order directly.
6. `DELIVERED` is a physical fact and starts buyer protection. `COMPLETED` is a financial fact and releases held funds.
7. Querysets must enforce role/object ownership; UI visibility is never authorization.
8. Scheduled tasks must be safe to execute more than once.

## Mandatory separation of concerns

Dependencies flow inward only: API views → application/domain services → models and repositories. External provider adapters normalize untrusted payloads before services see them. Models never call HTTP providers. Finance services never depend on API requests. Logistics and returns may request a financial command through an outbox event but may not mutate ledger or wallet balances directly. Notification, search, cache, and media work are outbox consumers and never participate in the originating transaction. Serializers shape data but contain no cross-model workflow. Scheduled workers call the same services as APIs, preserving one business-rule implementation.

## Commerce lifecycle

Checkout locks product rows, validates availability, snapshots lines, creates a pending order, reserves inventory for 20 minutes, and creates one fulfillment per seller. The buyer creates an idempotent payment attempt. A verified captured provider event consumes the reservation, deducts physical inventory, creates a financial snapshot, and marks the order paid.

Sellers advance only their fulfillment. Once all sellers satisfy the readiness gate, delivery can begin. Delivery starts the buyer-protection deadline. Buyer receipt confirmation or trusted protection-expiry processing completes the order unless a dispute blocks it.

The canonical state contracts and native integration rules are maintained below in this guide.

## Adding an API feature

1. Add domain models and database constraints.
2. Generate and inspect a migration.
3. Put cross-model behavior in an atomic service.
4. Define explicit serializer writable/read-only fields.
5. Add a role-scoped view reachable through `/api/v1/` when mobile-relevant.
6. Test success, invalid states, ownership, replay and rollback.
7. Document compatibility and operational impact.

## Local validation

The local environment may require a valid boolean DEBUG override:

```powershell
$env:DEBUG='True'
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Apply committed migrations with `python manage.py migrate`. Production must configure `DEBUG=False`, a strong secret, allowed hosts/CORS origins, webhook secrets, HTTPS and production database credentials.

## Role boundaries

- Buyers browse, purchase, track, confirm, review, cancel eligible lines, and request returns. They never see seller margins, platform controls, or other buyers' data.
- Sellers manage their store, listings, inventory, owned fulfillment lines, evidence, and earnings. They never see another seller's fulfillment or platform-wide finances.
- Couriers access only assigned deliveries and custody operations.
- Administrators moderate identities, products, disputes, payouts, and configuration. Administrative authority is audited and does not bypass ledger invariants.

Backend permissions and role-filtered querysets are authoritative. Frontend route guards are usability controls only.

## Canonical commerce states

- Order: `PENDING → PAID → READY_FOR_DELIVERY → IN_TRANSIT → DELIVERED → COMPLETED`, with cancellation, dispute, expiry, refund, and partial-refund branches.
- Reservation: `ACTIVE → CONSUMED | RELEASED | EXPIRED`.
- Seller fulfillment: `AWAITING_ACCEPTANCE → ACCEPTED → PICKING → PACKED → READY_FOR_PICKUP → HANDED_OVER`.
- Delivery: `REQUESTED → ASSIGNED → PICKED_UP → IN_TRANSIT → OUT_FOR_DELIVERY → DELIVERED`, with failed, exception, returned, lost, and cancelled branches.
- Return: `REQUESTED → APPROVED → COURIER_ASSIGNED → PICKED_UP → IN_TRANSIT → SELLER_RECEIVED → CONDITION_VERIFIED → REFUND_AUTHORIZED → CLOSED`.
- Payment: `CREATED → CAPTURED | FAILED | REFUNDED`.
- Escrow: held funds may be released, frozen, partially refunded, or refunded; every money movement must have balanced ledger entries.

`DELIVERED` records a physical fact. `COMPLETED` records the end of buyer protection and financial settlement.

## Mobile API v1

Native clients use `/api/v1/`; unversioned `/api/` remains for the current web client. Requests use JSON and `Authorization: Bearer <JWT>`. List responses use DRF pagination with `count`, `next`, `previous`, and `results`. Clients must ignore unknown additive response fields.

Checkout submits address and `items[{product, quantity}]`; the server owns prices, sellers, totals, taxes, fees, stock, and status. `POST /api/v1/orders/{id}/payment-attempts/` requires an `Idempotency-Key`. Development environments may enable `POST /api/v1/orders/{id}/simulate-payment/`; production must set `PAYMENT_SIMULATION_ENABLED=False`. Clients must never infer payment success from a provider UI.

Seller fulfillment is available under `/api/v1/fulfillments/`; returns under `/api/v1/returns/`; deliveries, notifications, reviews, RFQs, profiles, addresses, products, and locations are also composed under v1. `/api/v1/meta/` exposes server time, compatibility, currency, and feature flags.

Offline clients may cache catalog displays but must revalidate stock and price at checkout. Retry only idempotent commands and reuse the same idempotency key for the same user action.

## KYC and identity

Users verify phone and email ownership. Buyers maintain saved delivery addresses. Sellers additionally provide business type, legal/business name, registration number, TPIN, physical location, payout provider, account name, and account number. Seller verification proceeds through pending, submitted, review, verified, or rejected states. Couriers have their own verified delivery-partner profile.

Only verified sellers may publish active products. Payouts require verified identity and must ultimately use a fresh OTP challenge. Sensitive identity and payout data must be encrypted or provider-tokenized in production, excluded from logs, and visible only to authorized staff.

Seller approval has no direct boolean shortcut. Both phone and email must be verified; the business type, legal name, TPIN, operating address/zone, payout method/provider/account ownership, government ID front/back, and selfie with ID must be present. Partnerships and companies also require a registration number. The seller explicitly attests accuracy and consents to identity checks. Staff separately confirms that the payout account belongs to the verified identity, then executes the guarded KYC approval transition. Changing identity-sensitive business, address, tax, or payout data revokes verification, disables payout ownership, suspends active products, and requires a new review.

Buyers use proportionate KYC: phone and email ownership are required before checkout and seller KYC submission, while government ID is not required for ordinary purchases. Higher-risk actions may introduce step-up verification later without burdening initial browsing and registration.

## Product media and design

Buyer profile images are optional. Seller logo and banner media are part of store trust and should be reviewed during onboarding. Products support multiple images with one primary image and a maximum enforced by the model. Production media should use object storage, generated thumbnail/WebP derivatives, file-type and size validation, metadata stripping, and CDN delivery; the relational database stores references rather than image bytes.

The UI is mobile-first. Preserve accessible contrast, minimum 44px touch targets, responsive grids, keyboard navigation, explicit loading/error states, and reduced-motion preferences. Optimize for constrained 3G/4G connections by limiting payloads and responsive image sizes.

## Physical logistics and shipping

Products store actual weight, package dimensions, shipping class, and tax category. Shipping quotes use the larger of actual and dimensional weight against versioned rates. Packages belong to one seller fulfillment and snapshot measurements, declared value, chosen rate, and fee.

Bus and third-party deliveries use append-only custody events recording releasing and receiving parties, location, waybill, seal, verification method, actor, and timestamp. Physical returns are separate from disputes and refunds. A return inspection authorizes a financial command through the outbox; logistics never edits ledger balances directly.

## Financial rules

Payment capture, refunds, commission, tax, seller/courier liabilities, releases, penalties, and payouts belong to finance services. Ledger transactions and entries are append-only, use unique references, explicit currency, and equal debit/credit totals. Cached escrow and wallet balances are projections that must reconcile to the ledger.

The tax engine must snapshot seller tax status, product tax category, rate, net amount, and tax amount at checkout. Invoices require stable sequences and refunds require linked credit notes. ZRA fiscal requirements must be verified against current official guidance before live issuance.

## Reliability and operations

The database is the authority for money, inventory, and workflow state. Redis, search indexes, and CDN projections may accelerate reads but cannot authorize checkout. Cross-model commands use atomic transactions and row locks. External callbacks require signature verification, amount/currency validation, unique event identifiers, and replay-safe handling.

The transactional outbox publishes notifications and future search, cache, media, reconciliation, and provider work after commit. Consumers record processed events and retry failures with bounded backoff. Scheduled jobs expire reservations, complete buyer protection, dispatch outbox events, monitor delivery SLAs, and reconcile financial projections.

Production requires PostgreSQL, HTTPS, secure secrets, `DEBUG=False`, restricted hosts/CORS, API throttling/WAF, health checks, metrics, backups, restore tests, worker supervision, and provider sandbox certification.

## Privacy and retention

Privacy exports should gather profile, addresses, orders, reviews, disputes, and notifications into an encrypted, expiring download. Account deletion revokes access and anonymizes removable personal data while retaining pseudonymous order, tax, ledger, audit, and dispute records required for legal or fraud purposes. Evidence under legal hold is not deleted prematurely.

## Frontend map

Public pages include the storefront, product detail, category pages, registration, sign-in, about, contact, privacy, and terms. Buyer pages include cart, checkout, orders, order detail, profile, wishlist, and dashboard. Seller operations include onboarding, dashboard, products, orders/fulfillment, earnings, disputes, store, and profile. Administrative pages cover users, products, orders, disputes, finances, courier payouts, reports, settings, and audit logs.

## MVP readiness checklist

Before a pilot: apply migrations; seed locations, categories, verified sellers, active products, shipping and commission rates; enable simulated payments only in the pilot environment; run the complete test suite; test buyer checkout through receipt/return; test seller fulfillment; test courier assignment and custody; dispatch the outbox worker; verify ledger balance; configure backups and error monitoring; and document support/escalation ownership.

## Launch MVP scope

The launch rule is: if a capability does not directly enable exchanging a physical product for money, it is not a launch dependency. PostgreSQL is the transactional authority and provides partial-string/category search for the initial catalog. Celery and Redis run reservation expiry, outbox dispatch, notifications, protection expiry, and reconciliation work. Production media uses S3-compatible object storage when `USE_S3=True`.

Buyer launch flow: JWT authentication, public product feed, category/search filters, server-priced checkout, flat zone shipping, idempotent payment attempt, simulated payment until provider certification, text order/delivery statuses, receipt confirmation, and a simple support/return request.

Seller launch flow: manual administrative KYC approval, product CRUD with constrained images, owned fulfillment work, pack/ready controls, earnings visibility, and manual withdrawal requests. Administrators export pending payout requests to CSV for weekly processing through the provider corporate portal.

Logistics launch flow: configured flat delivery zones, manual courier assignment, picked-up/in-transit/delivered updates, optional bus waybill custody evidence, and a 14-day protection clock from delivery.

Delivery fees are buyer-paid by default and snapshotted per leg. Depot collection charges only the configured zone/inter-district fee. Origin pickup is optional when a seller cannot deliver to the dispatch depot; destination last mile is optional when the buyer does not want depot collection. Yango or another local rider is a replaceable provider for either local leg, never a mandatory carrier. Seller- or platform-funded shipping promotions must be explicit ledger subsidies rather than hidden deductions.

Advanced volumetric quotes, automated reverse logistics, automated payout APIs, complex dispute automation, OpenSearch, and live-map tracking may remain in the codebase as isolated extension points but must not block or complicate the MVP user journey. They remain disabled operationally until pilot volume and unit economics justify activation.

### Worker commands

After installing requirements, run Redis and then start workers with `celery -A config.celery worker -l INFO`. Schedule the functions documented in `apps/tasks/async_tasks.py` using Celery Beat or the deployment scheduler. Webhook endpoints should validate and persist quickly; slow provider calls and notifications belong in workers.

### Manual payouts

Verified sellers use `GET|POST /api/v1/sellers/payout_requests/`. Requests cannot exceed available escrow. Staff review them in Django admin and use the CSV export action; exported requests are marked `EXPORTED`, and staff records `PAID` plus the provider reference after portal confirmation.

## Documentation policy

`README.md` is the concise setup and project entry point. `CODEBASE_GUIDE.md` is the authoritative backend architecture and operations reference. `MOBILE_APP.md` is the consolidated mobile API and screen contract. Update these files with material changes; do not create Markdown status or completion documents.
