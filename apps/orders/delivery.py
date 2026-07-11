"""MVP delivery quoting. Checkout and clients share this single price authority."""
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.logistics.models import ZambianLocation

def quote_delivery(*, zone_id, origin_pickup_required=False, destination_delivery_required=False):
    try:
        zone = ZambianLocation.objects.get(pk=zone_id, location_type='ZONE', is_active=True)
    except ZambianLocation.DoesNotExist as exc:
        raise ValidationError('Select an active delivery zone.') from exc
    base = zone.delivery_base_cost
    origin = Decimal(str(getattr(settings, 'MVP_ORIGIN_PICKUP_FEE', '40.00'))) if origin_pickup_required else Decimal('0.00')
    destination = Decimal(str(getattr(settings, 'MVP_DESTINATION_LAST_MILE_FEE', '40.00'))) if destination_delivery_required else Decimal('0.00')
    service = 'DOOR_TO_DOOR' if origin_pickup_required and destination_delivery_required else ('DEPOT_TO_DOOR' if destination_delivery_required else ('DOOR_TO_DEPOT' if origin_pickup_required else 'DEPOT_COLLECTION'))
    return {'zone_id': zone.id, 'zone_name': zone.get_full_address(), 'delivery_service': service,
            'origin_pickup_fee': origin, 'inter_district_fee': base,
            'destination_delivery_fee': destination, 'delivery_fee': origin + base + destination}
