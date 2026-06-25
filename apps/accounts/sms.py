from django.conf import settings
from apps.common.models import AuditLog


def send_sms(phone_number: str, message: str) -> bool:
    """Send SMS using configured provider. Falls back to audit log in DEBUG or when no provider configured.

    Returns True on success, False otherwise.
    """
    provider = getattr(settings, 'SMS_PROVIDER', None)
    if provider == 'TWILIO':
        try:
            from twilio.rest import Client
        except Exception:
            AuditLog.objects.create(actor=None, action='SMS_FAIL', target_type='User', target_id=0, details={'phone': phone_number, 'reason': 'twilio_not_installed'})
            return False

        sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        from_number = getattr(settings, 'TWILIO_FROM_NUMBER', None)
        if not sid or not token or not from_number:
            AuditLog.objects.create(actor=None, action='SMS_FAIL', target_type='User', target_id=0, details={'phone': phone_number, 'reason': 'twilio_not_configured'})
            return False

        try:
            client = Client(sid, token)
            client.messages.create(body=message, from_=from_number, to=phone_number)
            AuditLog.objects.create(actor=None, action='SMS_SENT', target_type='User', target_id=0, details={'phone': phone_number})
            return True
        except Exception as exc:
            AuditLog.objects.create(actor=None, action='SMS_FAIL', target_type='User', target_id=0, details={'phone': phone_number, 'error': str(exc)})
            return False

    # Default fallback: log to AuditLog when in DEBUG, otherwise no-op but record
    if getattr(settings, 'DEBUG', False):
        AuditLog.objects.create(actor=None, action='SMS_SENT_DEBUG', target_type='User', target_id=0, details={'phone': phone_number, 'message': message})
        return True

    AuditLog.objects.create(actor=None, action='SMS_UNDELIVERED', target_type='User', target_id=0, details={'phone': phone_number, 'message_preview': message[:80]})
    return False
