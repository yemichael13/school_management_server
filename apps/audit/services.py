from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from .models import AuditLog


class AuditService:
    @staticmethod
    def _safe(value):
        if isinstance(value, (UUID, Decimal, date, datetime)):
            return str(value)
        if isinstance(value, dict):
            return {str(key): AuditService._safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [AuditService._safe(item) for item in value]
        return value

    @staticmethod
    def record(*, action, entity_type, entity_id=None, actor=None, school=None, before=None, after=None, request=None):
        return AuditLog.objects.create(
            actor=actor,
            school=school,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before=AuditService._safe(before),
            after=AuditService._safe(after),
            request_id=(request.META.get('HTTP_X_REQUEST_ID', '') if request else ''),
            ip_address=AuditService._ip(request) if request else None,
        )

    @staticmethod
    def _ip(request):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        return forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')
