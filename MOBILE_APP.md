# Optimistic Mobile Application Contract

This document defines the React Native/Expo mobile screens and Django `/api/v1/` integration. Django remains authoritative for price, stock, order state, payment, fulfillment, delivery, escrow, and permissions.

The responsive web client uses React + Vite + JavaScript, React Router, TanStack Query, Zustand, Django REST Framework, and controlled polling. Its visual system uses light-blue surfaces, restrained purple actions/status accents, and warm yellow conversion highlights. Web and native clients share API terminology and state behavior, not UI components.

## Navigation and screens

Public stack: Splash/compatibility check, sign in, registration, contact verification, product feed, category results, search, product detail, seller store, terms and privacy.

Buyer tabs: Home, Search, Cart, Orders, Account. Buyer detail screens: checkout address and zone, order review, payment processing, payment result, order timeline, delivery detail, confirm receipt, cancel line, report issue/return, notifications, addresses, verification, and profile.

Seller tabs: Dashboard, Products, Fulfillment, Earnings, Account. Seller detail screens: onboarding/KYC, create/edit product, image manager, fulfillment detail, pack/ready/handover, return detail, payout request, payout history, notifications, and store profile.

Courier tabs: Assigned, History, Notifications, Account. Courier detail screens: delivery detail, pickup confirmation, custody/waybill capture, transit update, delivery confirmation, exception reporting, and registration/verification.

Administrators use the web administration interface for MVP moderation, courier assignment, KYC, disputes, and payout CSV export.

## API conventions

Base URL: `/api/v1/`. Use JSON, ISO-8601 UTC timestamps, ZMW currency, DRF pagination, and `Authorization: Bearer <access>`. Refresh through `/auth/token/refresh/`. Store native refresh tokens in Expo SecureStore/Keychain, never AsyncStorage. Call `/meta/` at startup for compatibility and server time.

Core resources: `/products/`, `/categories/`, `/sellers/`, `/orders/`, `/fulfillments/`, `/deliveries/`, `/returns/`, `/notifications/`, `/reviews/`, `/locations/`, and `/rfq/`.

Checkout sends `items[{product, quantity}]`, address, zone, and instructions. It never sends authoritative prices or totals. Create payment through `/orders/{id}/payment-attempts/` with `Idempotency-Key`. Development may call `/orders/{id}/simulate-payment/`; production must disable it. Confirm receipt at `/orders/{id}/confirm-receipt/`, cancel a line at `/orders/{id}/cancel-line/`, and create physical returns through `/returns/`.

Seller fulfillment transitions use `/fulfillments/{id}/transition/`. Manual payout requests use `GET|POST /sellers/payout_requests/`. Couriers read assigned `/deliveries/` and append delivery events through `/deliveries/{id}/events/`.

## Client states and reliability

Every screen supports loading, empty, offline, validation, authorization, retryable failure, and terminal-success states. TanStack Query owns server state; a small Zustand store owns only local cart/UI state. On resume, refresh active payment, order, fulfillment, delivery, and notification queries.

Use controlled polling for MVP: payment every 3–5 seconds while processing, active delivery every 20 seconds, and unread notifications every 60 seconds. Stop polling for terminal states and while backgrounded. Future WebSocket events only trigger query invalidation; REST remains authoritative.

All retryable commands use stable idempotency keys. Never infer payment success from the provider UI, and never optimistically display a commercial state transition until Django confirms it.

## Realtime event contract

Future Channels events use `{type, event_id, occurred_at, data}`. Initial types: `payment.updated`, `order.status_changed`, `fulfillment.updated`, `delivery.updated`, and `notification.created`. Clients deduplicate `event_id`, invalidate matching queries, and fall back to polling after disconnects.
