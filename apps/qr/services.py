import hashlib
import secrets
from hmac import compare_digest

from django.db import transaction
from django.utils import timezone

from .models import QRToken, QRVerificationEvent
from apps.audit.services import AuditService


class QRVerificationService:
    @staticmethod
    def generate_token(*, report_version):
        raw_token = secrets.token_urlsafe(48)
        token = QRToken(report_version=report_version, token_hash=QRToken.hash_token(raw_token))
        token.full_clean()
        token.save()
        return raw_token, token

    @staticmethod
    def _client_ip(request):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        return forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')

    @staticmethod
    @transaction.atomic
    def verify(*, raw_token, request=None):
        raw_token = (raw_token or '').strip()
        token_hash = QRToken.hash_token(raw_token) if raw_token else ''
        token = QRToken.objects.select_related('report_version__report_card__report_period', 'report_version__report_card__enrollment__student').filter(token_hash=token_hash).first()
        if not token and len(raw_token) == 64:
            token = QRToken.objects.select_related('report_version__report_card__report_period', 'report_version__report_card__enrollment__student').filter(token_hash=raw_token).first()
        ip_address = QRVerificationService._client_ip(request) if request else None
        user_agent_hash = hashlib.sha256((request.META.get('HTTP_USER_AGENT', '') if request else '').encode()).hexdigest() if request else ''
        if not token:
            QRVerificationEvent.objects.create(qr_token=None, attempted_token_hash=token_hash, result=QRVerificationEvent.Result.INVALID, ip_address=ip_address, user_agent_hash=user_agent_hash)
            AuditService.record(action='qr_verification', entity_type='qr_token', actor=None, after={'result': QRVerificationEvent.Result.INVALID}, request=request)
            return {'authentic': False, 'status': 'invalid', 'report': None}
        if not compare_digest(token.token_hash, token_hash) and not compare_digest(token.token_hash, raw_token):
            result = QRVerificationEvent.Result.INVALID
        elif token.revoked_at or not token.is_active:
            result = QRVerificationEvent.Result.REVOKED
        elif token.expires_at and token.expires_at <= timezone.now():
            result = QRVerificationEvent.Result.EXPIRED
        elif token.report_version.report_card.status != 'published':
            result = QRVerificationEvent.Result.INVALID
        else:
            result = QRVerificationEvent.Result.SUCCESS
        QRVerificationEvent.objects.create(qr_token=token, attempted_token_hash=token_hash, result=result, ip_address=ip_address, user_agent_hash=user_agent_hash)
        AuditService.record(action='qr_verification', entity_type='qr_token', entity_id=token.id, school=token.report_version.report_card.enrollment.student.school, after={'result': result}, request=request)
        if result != QRVerificationEvent.Result.SUCCESS:
            return {'authentic': False, 'status': result, 'report': None}
        report_card = token.report_version.report_card
        latest = report_card.versions.filter(published_at__isnull=False).order_by('-version_no').first() or token.report_version
        return {
            'authentic': True,
            'status': 'authentic',
            'report': {
                'school_name': report_card.enrollment.student.school.name,
                'student_name': report_card.enrollment.student.full_name,
                'report_period': report_card.report_period.name,
                'version': latest.version_no,
                'published_at': latest.published_at,
                'total': latest.total,
                'average': latest.average,
                'rank': latest.rank,
            },
        }
