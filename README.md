# Optimistic — Multi-Seller Marketplace

Optimistic is a trust-first Django and Django REST Framework marketplace designed for Zambian buyers, sellers, couriers, mobile-money payments, local delivery, escrow, returns, and disputes.

Engineering documentation is maintained in [CODEBASE_GUIDE.md](CODEBASE_GUIDE.md), with mobile screens and API integration in [MOBILE_APP.md](MOBILE_APP.md).

## Capabilities

- JWT authentication, contact verification, profiles, addresses, and role separation
- Seller KYC, storefronts, moderated products, media, stock, and reservations
- Atomic multi-seller checkout with simulated payment support
- Idempotent payment events and signed MTN/Airtel webhook boundaries
- Per-seller fulfillment, packages, shipping rates, couriers, bus custody, and returns
- Buyer protection, disputes, escrow, balanced ledger entries, and refund foundations
- Transactional outbox, notifications, reviews, RFQs, audit logs, and mobile `/api/v1/`

## Stack

- Python and Django
- Django REST Framework and Simple JWT
- SQLite for local development; PostgreSQL intended for production
- Vanilla HTML, CSS, and JavaScript frontend

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DEBUG='True'
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:

- Web application: `http://127.0.0.1:8000/`
- Administration: `http://127.0.0.1:8000/admin/`
- Mobile API metadata: `http://127.0.0.1:8000/api/v1/meta/`

## Development payment simulation

Set `PAYMENT_SIMULATION_ENABLED=True`, create an order and payment attempt, then use the documented `/api/v1/orders/{id}/simulate-payment/` endpoint. Simulation must be disabled in production.

## Validation

```powershell
$env:DEBUG='True'
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

## Documentation policy

- `README.md` is the concise setup and entry point.
- `CODEBASE_GUIDE.md` is the sole architecture, workflow, API, KYC, design, security, and operations reference.
- Do not add separate Markdown status or completion documents; update the guide instead.

Proprietary. All rights reserved.
