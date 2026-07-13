# Optimistic — Multi-Seller Marketplace

Optimistic is a trust-first Django and React marketplace for Zambian buyers, sellers, couriers, mobile-money payments, local/inter-district delivery, escrow, returns, and disputes.

The authoritative engineering reference is [CODEBASE_GUIDE.md](CODEBASE_GUIDE.md). Native mobile screens and the stable `/api/v1/` contract are documented in [MOBILE_APP.md](MOBILE_APP.md).

## Capabilities

- JWT authentication, phone/email verification, saved addresses, legal acceptance, and role isolation
- Seller KYC, schema-driven product specifications, media, moderation, inventory, and analytics
- Atomic multi-seller checkout, inventory reservations, idempotent payment attempts, and simulated payments
- Seller fulfillment, optional local delivery, inter-district carriers, bus custody, returns, and delivery exceptions
- Buyer protection, disputes, escrow freezes, immutable double-entry ledger foundations, refunds, and payout requests
- Transactional outbox, notifications, audit logs, reviews, RFQs, Django administration, and mobile `/api/v1/`

## Stack

- Django, Django REST Framework, Simple JWT, and PostgreSQL for production
- SQLite for local development
- React + Vite + JavaScript, React Router, TanStack Query, and Zustand
- Controlled HTTP polling for MVP payment, fulfillment, delivery, and notification updates

## Backend quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env -ErrorAction SilentlyContinue
python manage.py migrate
python manage.py seed_locations
python manage.py seed_demo_data
python manage.py runserver 0.0.0.0:8000
```

Open:

- Django: `http://127.0.0.1:8000/`
- Administration: `http://127.0.0.1:8000/admin/`
- Mobile API metadata: `http://127.0.0.1:8000/api/v1/meta/`

Create an administrator separately:

```powershell
python manage.py createsuperuser
```

## React web client

Start Django and Vite together from the repository root:

```powershell
.\dev.ps1
```

Alternatively, from `client/`:

```powershell
npm run dev:full
```

For separate terminals:

```powershell
cd client
npm install
npm run dev
```

The Vite development client runs at `http://localhost:5173` and proxies `/api` to Django at `127.0.0.1:8000`. A Vite `ECONNREFUSED 127.0.0.1:8000` message means Django is not running; use the combined launcher or start `python manage.py runserver 127.0.0.1:8000` separately. Build the production bundle with `npm run build`.

## Demo data

The default generator creates a reproducible marketplace dataset with verified buyer contacts, seller accounts, saved Zambia-zone addresses, structured products, multi-seller order lines, fulfillment records, reviews, and notifications:

```powershell
python manage.py seed_demo_data `
  --buyers 30 `
  --sellers 15 `
  --products 150 `
  --orders 300 `
  --seed 260
```

Use larger target values for load-oriented UI testing. Re-running reaches the requested product/order totals and backfills missing legacy order lines instead of blindly duplicating the whole dataset.

Demo credentials:

```text
Buyer: john_buyer / buyer123
Seller: techstore / seller123
```

Never run demo seeding against production. `--clear` removes non-staff demo commerce data and is intended only for disposable local databases.

## Mobile testing

Start Django on `0.0.0.0:8000`. Use one of these API base URLs:

- Postman/web/iOS simulator: `http://127.0.0.1:8000/api/v1`
- Android emulator: `http://10.0.2.2:8000/api/v1`
- Physical device: `http://<computer-LAN-IP>:8000/api/v1`

The phone and computer must share a network, and the LAN address must be present in local `ALLOWED_HOSTS`. Obtain the current Windows address with `ipconfig`.

## Development payment simulation

Keep `PAYMENT_SIMULATION_ENABLED=True` only in local/test configuration. Create an order, create `/api/v1/orders/{id}/payment-attempts/` with an `Idempotency-Key`, then call `/api/v1/orders/{id}/simulate-payment/`. Production must explicitly disable simulation.

## Validation

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
cd client
npm run build
```

## Documentation policy

- `README.md` is the concise setup and project entry point.
- `CODEBASE_GUIDE.md` is the authoritative architecture and operations reference.
- `MOBILE_APP.md` is the mobile screen and API contract.
- Do not add separate status/completion Markdown files; update these documents.

Proprietary. All rights reserved.
