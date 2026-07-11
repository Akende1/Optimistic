"""Atomic accounting services. Ledger postings are append-only and balanced."""
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from .models import LedgerEntry, LedgerTransaction


@transaction.atomic
def post_transaction(*, reference, event_type, currency, entries, order=None, metadata=None):
    existing = LedgerTransaction.objects.filter(reference=reference).first()
    if existing:
        return existing, False
    debit = sum((Decimal(str(e['amount'])) for e in entries if e['side'] == 'DEBIT'), Decimal('0.00'))
    credit = sum((Decimal(str(e['amount'])) for e in entries if e['side'] == 'CREDIT'), Decimal('0.00'))
    if debit <= 0 or debit != credit:
        raise ValidationError(f'Unbalanced ledger transaction: debits={debit}, credits={credit}.')
    ledger_tx = LedgerTransaction.objects.create(
        reference=reference, event_type=event_type, currency=currency,
        order=order, metadata=metadata or {},
    )
    LedgerEntry.objects.bulk_create([
        LedgerEntry(transaction=ledger_tx, account=e['account'], side=e['side'],
                    amount=Decimal(str(e['amount'])), seller=e.get('seller'), courier=e.get('courier'))
        for e in entries
    ])
    return ledger_tx, True


def assert_transaction_balanced(ledger_tx):
    debits = ledger_tx.entries.filter(side='DEBIT').aggregate(v=Sum('amount'))['v'] or Decimal('0.00')
    credits = ledger_tx.entries.filter(side='CREDIT').aggregate(v=Sum('amount'))['v'] or Decimal('0.00')
    if debits != credits:
        raise ValidationError('Ledger transaction is not balanced.')
    return True


def post_payment_capture(attempt):
    return post_transaction(
        reference=f'payment-capture:{attempt.id}', event_type='PAYMENT_CAPTURE',
        currency=attempt.currency, order=attempt.order,
        entries=[
            {'account': 'PAYMENT_PROVIDER_CLEARING', 'side': 'DEBIT', 'amount': attempt.amount},
            {'account': 'CUSTOMER_ESCROW_LIABILITY', 'side': 'CREDIT', 'amount': attempt.amount},
        ],
    )


def post_refund(*, order, order_item, amount, reference):
    return post_transaction(
        reference=reference, event_type='CUSTOMER_REFUND', currency=order.currency, order=order,
        metadata={'order_item_id': order_item.id},
        entries=[
            {'account': 'CUSTOMER_ESCROW_LIABILITY', 'side': 'DEBIT', 'amount': amount},
            {'account': 'PAYMENT_PROVIDER_CLEARING', 'side': 'CREDIT', 'amount': amount},
        ],
    )
