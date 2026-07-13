# Optimistic Mobile Application Contract

This document defines the React Native/Expo mobile screens and Django `/api/v1/` integration. Django remains authoritative for price, stock, order state, payment, fulfillment, delivery, escrow, and permissions.

The responsive web client uses React + Vite + JavaScript, React Router, TanStack Query, Zustand, Django REST Framework, and controlled polling. Its visual system uses light-blue surfaces, restrained purple actions/status accents, and warm yellow conversion highlights. Web and native clients share API terminology and state behavior, not UI components.

## Navigation and screens

Public stack: Splash/compatibility check, sign in, registration, contact verification, product feed, category results, search, product detail, seller store, terms and privacy.

Buyer tabs: Home, Search, Cart, Orders, Account. Buyer detail screens: checkout address and zone, order review, payment processing, payment result, order timeline, delivery detail, confirm receipt, cancel line, report issue/return, notifications, addresses, verification, and profile.

Seller tabs: Dashboard, Products, Fulfillment, Earnings, Account. Seller detail screens: onboarding/KYC, create/edit product, image manager, fulfillment detail, pack/ready/handover, return detail, payout request, payout history, notifications, and store profile.

Courier tabs: Assigned, History, Notifications, Account. Courier detail screens: delivery detail, pickup confirmation, custody/waybill capture, transit update, delivery confirmation, exception reporting, and registration/verification.

Administrators use the web administration interface for MVP moderation, courier assignment, KYC, disputes, and payout CSV export.

### Shared and public screens

| Screen | Purpose and required states |
|---|---|
| Splash and compatibility | Load `/meta/`, restore credentials, refresh an expired access token, enforce minimum supported app version, and route by role. Show offline retry and maintenance states. |
| Welcome and authentication | Sign in, registration, password reset request/confirm, logout, expired-session recovery, and role selection. Registration records separate Terms and Privacy acknowledgement. |
| Contact verification | Request and confirm phone or email OTP. Show cooldown, expiry, invalid-code, already-verified, and resend states. Sellers must verify both channels before KYC. |
| Legal centre | Platform Terms, Privacy Notice, and Seller Terms from `/legal/`; record acceptance through `/legal/accept/`. Legal content must remain readable without authentication. |
| Product discovery | Home feed, categories, search, sorting, filters, pagination/infinite scroll, recently viewed products, and empty/offline states. |
| Product detail | Images, structured category specifications, condition, stock, seller, shipping measurements/class, price, quantity, add-to-cart, and unavailable/moderated states. |
| Seller storefront | Public verified seller identity, store details, active listings, and contact/support boundaries without exposing KYC or payout data. |
| Notifications | Paginated inbox, unread count, mark-read action, deep links, permission prompt, and 60-second foreground polling. |
| Account and security | Profile, contact status, password change, active-session logout, legal links, privacy export/deletion request, and support entry. |

### Buyer screens

| Screen | Purpose and API responsibility |
|---|---|
| Cart | Local Zustand cart with server product refresh before checkout. Handle price/stock changes, removed products, quantities, seller grouping, and persistent restoration. |
| Address book | List, create, edit, select, and remove saved addresses; choose a valid district/zone returned by `/locations/`. |
| Delivery options | Select depot collection or optional destination last mile; show optional seller-origin pickup and inter-district legs. Yango/local rider is optional. Display who pays each fee before order creation. |
| Checkout review | Submit products, quantities, address, zone and delivery choices for server pricing. Render product subtotal, each delivery leg, tax where applicable, and total from the response. Never calculate the authoritative total locally. |
| Payment method | Select simulated payment in development or an enabled MTN/Airtel provider later; enter the payer number and create an idempotent payment attempt. |
| Payment processing | Poll the attempt every 3–5 seconds, tolerate background/resume, and show pending-provider, success, failure, expiry, retry, and duplicate-submission states. |
| Payment result | Show confirmed order reference and next action only after Django reports success. Failed payments retain a safe retry path without recreating the order. |
| Orders | Paginated order list with status, date, total, active/completed filters, and empty state. |
| Order detail and timeline | Server totals, lines grouped by seller, payment state, fulfillment state, delivery legs, custody/waybill evidence, status history, and support actions. |
| Delivery tracking | Text-first delivery state, carrier, tracking/waybill reference, latest custody location/event, ETA where supplied, exception state, and 20-second active polling. |
| Confirm receipt | Explain buyer-protection impact, require explicit confirmation, prevent repeated commands, and refresh order/escrow state. |
| Line cancellation | Select eligible quantity and reason; show server-calculated cancellation/refund result. Disable ineligible delivered or already-cancelled quantities. |
| Return or issue | Choose line, quantity, reason, description, and evidence; show return state from requested through courier assignment, seller receipt, inspection, and refund outcome. |
| Wishlist | Optional MVP module. If retained, synchronize authenticated items and gracefully preserve a guest list; otherwise omit the tab and routes completely. |

### Seller screens

| Screen | Purpose and API responsibility |
|---|---|
| Seller Terms gate | Display current Seller Terms version, record explicit acceptance, and route to KYC only after success. |
| Onboarding and KYC | Business type/name, registration number where required, TPIN, physical location, payout owner/provider/account, government ID front/back, and selfie-with-ID. Show draft, submitted, pending, rejected with reason, and verified states. |
| Seller dashboard and analytics | Period selector for 7, 30, 90, or 365 days; net/gross sales, refunds, paid orders, units, available/pending balance, open fulfillment, low/out-of-stock counts, daily sales trend, and top five products from `/sellers/analytics/`. |
| Product list | Seller-owned drafts, pending, active, suspended and archived products; search/status filters, stock indicator, moderation reason, edit, archive, duplicate, and submit-for-approval actions. |
| Create/edit product | Base name, description, category, price, stock, weight, dimensions, shipping class, tax category, and category-schema fields returned by `/categories/`. Django is authoritative for required specifications and coercion. |
| Image manager | Camera/library selection, upload progress, reorder/primary selection, remove, retry, image count/size validation, and compressed mobile upload. |
| Inventory | Stock adjustment with reason, low-stock/out-of-stock views, and post-mutation analytics/product invalidation. Do not update stock optimistically. |
| Fulfillment queue | Poll seller-owned `/fulfillments/` every 15 seconds and group urgent/open/completed work. |
| Fulfillment detail | Seller lines only, acceptance deadline, buyer delivery instructions limited to what is operationally required, and valid accept → pick → pack → ready → handover actions. Include carrier/tracking capture where required. |
| Returns and disputes | Return custody, received-condition evidence, inspection decision, dispute/escrow-freeze state, requested evidence, and financial outcome. Logistics screens never directly alter balances. |
| Earnings | Available, pending and lifetime balances, ledger-derived earning events, deductions/refunds, and payout status. Avoid presenting gross marketplace order totals as seller earnings. |
| Withdrawal | Payout destination confirmation, amount, 2FA gate when enabled, available-balance validation, request receipt, and payout history/status/reference. |
| Store profile | Public store name/logo/description/location/contact plus separate protected business, tax and payout sections. Sensitive changes warn that re-verification may be required. |

#### Seller analytics contract

`GET /api/v1/sellers/analytics/?days=30` accepts a period from 7 to 365 days and returns `period`, `sales`, `products`, `fulfillments`, `balances`, `trend`, and `top_products`. Sales amounts are ZMW decimal strings. The endpoint is restricted to the authenticated seller and never returns buyer identity. Mobile seller dashboards should show net sales, units, available/pending balances, catalog health, top products, and daily trend data, with pull-to-refresh and 7/30/90/365-day filters.

### Courier screens

| Screen | Purpose and API responsibility |
|---|---|
| Courier registration and verification | Identity/contact, transport type, operating zones, partner/company association, required documents, terms, and pending/rejected/verified states. |
| Assigned deliveries | Seller-safe and buyer-safe assignment summary, pickup deadline, route type, priority, active/history filters, and refresh. |
| Delivery detail | Required pickup/drop-off information, package summary, contact controls, delivery legs, allowed next events, and proof requirements. |
| Pickup confirmation | Scan/enter package or handover code, capture time/location/evidence, and append a custody event. |
| Bus or third-party handover | Transit operator, station, destination, waybill/receipt, seal, releasing/receiving parties, photos, verification method, and append-only custody acknowledgement. |
| Transit updates | Picked up, in transit, arrived at depot, and out-for-delivery actions; prevent skipped or backwards transitions. |
| Delivery confirmation | OTP/signature/photo as configured, recipient identity relationship, timestamp/location, and server-confirmed completion. |
| Exception reporting | Failed contact, inaccessible address, damaged parcel, refused delivery, vehicle issue, delay, lost item, notes and evidence; show resulting operational instructions. |
| Courier earnings | Completed eligible work, pending/available amounts, adjustments, payout status, and reconciliation reference without seller financial data. |

### Required global state screens

The application also needs dedicated 401/session-expired, 403/role-forbidden, 404/not-found, forced-upgrade, maintenance, no-network, unexpected-error boundary, and notification-deep-link fallback screens. Every destructive or money-impacting command needs a confirmation sheet, disabled duplicate submission, server validation rendering, and a stable success receipt.

## API conventions

Base URL: `/api/v1/`. Use JSON, ISO-8601 UTC timestamps, ZMW currency, DRF pagination, and `Authorization: Bearer <access>`. Refresh through `/auth/token/refresh/`. Store native refresh tokens in Expo SecureStore/Keychain, never AsyncStorage. Call `/meta/` at startup for compatibility and server time.

Core resources: `/products/`, `/categories/`, `/sellers/`, `/orders/`, `/fulfillments/`, `/deliveries/`, `/returns/`, `/notifications/`, `/reviews/`, `/locations/`, and `/rfq/`.

Checkout sends `items[{product, quantity}]`, address, zone, and instructions. It never sends authoritative prices or totals. Create payment through `/orders/{id}/payment-attempts/` with `Idempotency-Key`. Development may call `/orders/{id}/simulate-payment/`; production must disable it. Confirm receipt at `/orders/{id}/confirm-receipt/`, cancel a line at `/orders/{id}/cancel-line/`, and create physical returns through `/returns/`.

Seller fulfillment transitions use `/fulfillments/{id}/transition/`. Manual payout requests use `GET|POST /sellers/payout_requests/`. Couriers read assigned `/deliveries/` and append delivery events through `/deliveries/{id}/events/`.

Seller analytics uses `GET /sellers/analytics/?days=30`. `days` is clamped to 7–365 and invalid non-integers return `400`. The response shape is:

```json
{
  "period": {"days": 30, "from": "2026-06-13", "to": "2026-07-12"},
  "sales": {"gross": "1250.00", "refunds": "50.00", "net": "1200.00", "orders": 8, "units_sold": 11},
  "products": {"total": 20, "active": 15, "low_stock": 3, "out_of_stock": 1, "by_status": {"ACTIVE": 15}},
  "fulfillments": {"open": 4, "by_status": {"PACKED": 2}},
  "balances": {"available": "700.00", "pending": "500.00", "lifetime_earnings": "9000.00"},
  "trend": [{"date": "2026-07-12", "gross_sales": "300.00", "orders": 2, "units_sold": 3}],
  "top_products": [{"product_id": 12, "name": "Example", "gross_sales": "600.00", "units_sold": 4}]
}
```

The endpoint is authenticated and seller-scoped. It excludes pending, failed, expired, cancelled, fully refunded, and other non-revenue states. Mobile code must treat decimal money values as decimal strings, not binary floating-point numbers.

Category objects include `attribute_schema`. Each field supplies `key`, `label`, `type`, `required`, and optional `options`/`min`. Render from that schema instead of hard-coding electronics or other category forms in the app. Initial schemas cover electronics/gadgets, vehicle parts, appliances, fashion, food, beauty, books, sports, and home/garden.

## Role routing and authorization

After authentication, route by the server user role. Route guards improve navigation but never replace API authorization. Buyers cannot open seller/courier work queues; sellers cannot read another seller’s products, lines, analytics, escrow or fulfillment; couriers receive only assigned delivery data; administration remains staff-only.

When an API returns `401`, attempt one token refresh and replay one safe request. On refresh failure, clear secure credentials and show session expired. For `403`, retain the session and show the role/verification requirement. For `409`, refresh the affected resource because another actor or retry may already have changed it.

## Query ownership and invalidation

Suggested TanStack Query keys are `['products', filters]`, `['product', id]`, `['orders', filters]`, `['order', id]`, `['payment-attempt', id]`, `['fulfillments']`, `['fulfillment', id]`, `['seller-analytics', days]`, `['deliveries', filters]`, `['delivery', id]`, `['notifications']`, and `['seller-kyc']`.

Product/stock mutations invalidate seller products and analytics. Fulfillment transitions invalidate the fulfillment list/detail, relevant order, and analytics. Payment success invalidates payment attempt, order list/detail, cart validation, and notifications. Delivery events invalidate delivery detail/list and the buyer order. Return/dispute changes invalidate return, order, relevant balances, analytics, and notifications.

## Mobile security and privacy

Use platform secure storage for refresh tokens and secrets. Do not log tokens, OTPs, government IDs, payout accounts, addresses, evidence URLs, or provider payloads. Blur or block screenshots on KYC and payout screens where supported. Remove temporary KYC/image files after upload, request the minimum camera/location permissions just in time, and explain why each is needed.

Do not cache KYC documents, full addresses, payout details, or dispute evidence in general AsyncStorage. Analytics and product caches may persist only if they contain no buyer identity. Clear all role-sensitive caches on logout or account switch.

## Accessibility, performance, and release acceptance

All controls require accessible labels, logical focus order, dynamic text support, sufficient contrast, and at least 44×44 point touch targets. Charts require textual totals and screen-reader summaries. Never convey status by colour alone. Respect reduced motion and support keyboard navigation where tablets or assistive input devices are used.

Compress product/evidence images before upload while preserving evidence legibility, use thumbnails in lists, paginate large resources, and avoid loading all trend/history data at once. The light-blue, purple-accent, warm-yellow visual language should remain consistent without sacrificing contrast.

Before mobile MVP release, contract-test authentication/refresh, registration consent, both OTP channels, server-priced checkout, idempotent simulated payment, payment resume, line cancellation, receipt confirmation, issue/return submission, seller KYC, schema-driven product creation with images, every fulfillment transition, seller analytics isolation, courier custody/waybill and exceptions, notification deep links, offline recovery, and role denial. Test at narrow phone and tablet sizes on Android first, then iOS, including constrained 3G conditions and app background/resume.

## Client states and reliability

Every screen supports loading, empty, offline, validation, authorization, retryable failure, and terminal-success states. TanStack Query owns server state; a small Zustand store owns only local cart/UI state. On resume, refresh active payment, order, fulfillment, delivery, and notification queries.

Use controlled polling for MVP: payment every 3–5 seconds while processing, active delivery every 20 seconds, and unread notifications every 60 seconds. Stop polling for terminal states and while backgrounded. Future WebSocket events only trigger query invalidation; REST remains authoritative.

All retryable commands use stable idempotency keys. Never infer payment success from the provider UI, and never optimistically display a commercial state transition until Django confirms it.

## Realtime event contract

Future Channels events use `{type, event_id, occurred_at, data}`. Initial types: `payment.updated`, `order.status_changed`, `fulfillment.updated`, `delivery.updated`, and `notification.created`. Clients deduplicate `event_id`, invalidate matching queries, and fall back to polling after disconnects.
