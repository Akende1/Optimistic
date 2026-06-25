import logging
from apps.common.models import AuditLog

logger = logging.getLogger(__name__)

def log_audit(actor, action, target_type, target_id, details=None, request=None):
    """
    Standardized helper to create audit logs without blocking the main flow.
    """
    ip_address = ''
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '')

    try:
        return AuditLog.objects.create(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details or {},
            ip_address=ip_address
        )
    except Exception as e:
        # Log the failure of the audit log itself to server logs, 
        # but don't crash the user's request.
        logger.error(f"Failed to create AuditLog: {str(e)}")
        return None