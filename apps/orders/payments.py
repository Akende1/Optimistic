"""Payment provider webhook verification adapters.

Adapters verify the raw request before normalized events enter commerce services.
Secrets are environment configuration and are never accepted in request bodies.
"""
import hashlib
import hmac
import json
from django.conf import settings
from django.core.exceptions import ValidationError


class HMACSHA256Adapter:
    signature_header = 'X-Webhook-Signature'

    def __init__(self, provider):
        self.provider = provider.upper()
        self.secret = settings.PAYMENT_WEBHOOK_SECRETS.get(self.provider, '')

    def verify_and_normalize(self, request):
        if not self.secret:
            raise ValidationError(f'{self.provider} webhook secret is not configured.')
        supplied = request.headers.get(self.signature_header, '')
        expected = hmac.new(self.secret.encode(), request.body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(supplied, expected):
            raise ValidationError('Invalid webhook signature.')
        try:
            payload = json.loads(request.body)
            return {
                'attempt_id': payload['attempt_id'],
                'external_event_id': str(payload['event_id']),
                'event_type': payload['event_type'],
                'payload': payload['data'],
            }
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValidationError('Malformed payment webhook payload.') from exc


class MTNMoMoAdapter(HMACSHA256Adapter):
    signature_header = 'X-MTN-Signature'


class AirtelMoneyAdapter(HMACSHA256Adapter):
    signature_header = 'X-Airtel-Signature'


ADAPTERS = {'MTN_MOMO': MTNMoMoAdapter, 'AIRTEL_MONEY': AirtelMoneyAdapter, 'TEST': HMACSHA256Adapter}


def get_adapter(provider):
    provider = provider.upper()
    adapter = ADAPTERS.get(provider)
    if not adapter:
        raise ValidationError('Unsupported payment provider.')
    return adapter(provider)
