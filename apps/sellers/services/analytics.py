from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count
from django.utils import timezone

from apps.orders.models import OrderItem
from apps.products.models import Product


REVENUE_ORDER_STATUSES = {
    'PAID', 'READY_FOR_DELIVERY', 'IN_TRANSIT', 'DELIVERED', 'COMPLETED',
    'DISPUTED', 'PARTIALLY_REFUNDED',
}


def build_seller_analytics(seller, days=30):
    """Return seller-scoped operational analytics from immutable order snapshots."""
    days = max(7, min(int(days), 365))
    since = timezone.now() - timedelta(days=days - 1)
    products = Product.objects.filter(seller=seller)
    lines = OrderItem.objects.filter(
        seller=seller, order__status__in=REVENUE_ORDER_STATUSES,
        order__created_at__gte=since,
    ).select_related('order', 'product')

    gross = Decimal('0.00')
    refunds = Decimal('0.00')
    units = 0
    order_ids = set()
    trend = defaultdict(lambda: {'gross_sales': Decimal('0.00'), 'orders': set(), 'units_sold': 0})
    top = defaultdict(lambda: {'name': '', 'gross_sales': Decimal('0.00'), 'units_sold': 0})

    for line in lines:
        sold_quantity = max(line.quantity - line.cancelled_quantity, 0)
        line_gross = line.price_snapshot * sold_quantity
        gross += line_gross
        refunds += line.refunded_amount
        units += sold_quantity
        order_ids.add(line.order_id)
        day = line.order.created_at.date().isoformat()
        trend[day]['gross_sales'] += line_gross
        trend[day]['orders'].add(line.order_id)
        trend[day]['units_sold'] += sold_quantity
        top[line.product_id]['name'] = line.product.name
        top[line.product_id]['gross_sales'] += line_gross
        top[line.product_id]['units_sold'] += sold_quantity

    product_statuses = {row['status']: row['count'] for row in products.values('status').annotate(count=Count('id'))}
    fulfillment_statuses = {
        row['status']: row['count']
        for row in seller.fulfillments.values('status').annotate(count=Count('id'))
    }
    escrow = getattr(seller, 'escrow_account', None)

    return {
        'period': {'days': days, 'from': since.date(), 'to': timezone.localdate()},
        'sales': {
            'gross': str(gross), 'refunds': str(refunds), 'net': str(gross - refunds),
            'orders': len(order_ids), 'units_sold': units,
        },
        'products': {
            'total': products.count(), 'active': product_statuses.get('ACTIVE', 0),
            'low_stock': products.filter(stock__gt=0, stock__lte=5).count(),
            'out_of_stock': products.filter(stock=0).count(), 'by_status': product_statuses,
        },
        'fulfillments': {
            'open': seller.fulfillments.exclude(status__in=['HANDED_OVER', 'REJECTED', 'CANCELLED']).count(),
            'by_status': fulfillment_statuses,
        },
        'balances': {
            'available': str(escrow.available_balance if escrow else Decimal('0.00')),
            'pending': str(escrow.pending_balance if escrow else Decimal('0.00')),
            'lifetime_earnings': str(escrow.lifetime_earnings if escrow else Decimal('0.00')),
        },
        'trend': [
            {'date': day, 'gross_sales': str(values['gross_sales']),
             'orders': len(values['orders']), 'units_sold': values['units_sold']}
            for day, values in sorted(trend.items())
        ],
        'top_products': sorted(
            ({'product_id': product_id, **values, 'gross_sales': str(values['gross_sales'])}
             for product_id, values in top.items()),
            key=lambda row: Decimal(row['gross_sales']), reverse=True,
        )[:5],
    }
