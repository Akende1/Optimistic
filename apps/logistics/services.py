"""Physical shipping quote and package construction services."""
from decimal import Decimal, ROUND_UP
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Package, ShippingRate


@transaction.atomic
def quote_fulfillment_package(*, fulfillment, service_code):
    items = list(fulfillment.order.items.filter(seller=fulfillment.seller).select_related('product'))
    if not items:
        raise ValidationError('Fulfillment has no active items.')
    classes = {item.product.shipping_class for item in items if item.active_quantity}
    shipping_class = 'OVERSIZED' if 'OVERSIZED' in classes else 'STANDARD'
    rate = ShippingRate.objects.filter(service_code=service_code, shipping_class=shipping_class,
                                       is_active=True, effective_from__lte=timezone.now()).first()
    if not rate:
        raise ValidationError('No active shipping rate is configured.')
    weight = sum((item.product.weight_kg * item.active_quantity for item in items), Decimal('0.000'))
    volume = sum((item.product.length_cm * item.product.width_cm * item.product.height_cm * item.active_quantity
                  for item in items), Decimal('0.00'))
    dim_weight = (volume / rate.dimensional_divisor).quantize(Decimal('0.001'), rounding=ROUND_UP)
    chargeable = max(weight, dim_weight)
    quoted = (rate.base_fee + rate.per_kg_fee * chargeable).quantize(Decimal('0.01'), rounding=ROUND_UP)
    declared = sum((item.price_snapshot * item.active_quantity for item in items), Decimal('0.00'))
    return Package.objects.create(
        fulfillment=fulfillment, shipping_rate=rate, weight_kg=weight,
        dimensional_weight_kg=dim_weight, chargeable_weight_kg=chargeable,
        length_cm=max(item.product.length_cm for item in items),
        width_cm=max(item.product.width_cm for item in items),
        height_cm=sum((item.product.height_cm for item in items), Decimal('0.00')),
        quoted_fee=quoted, declared_value=declared,
    )
