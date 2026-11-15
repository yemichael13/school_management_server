import hashlib
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from apps.core.models import UUIDTimestampedModel
from apps.reports.models import ReportCardVersion, ReportCard

class QRToken(UUIDTimestampedModel):
    report_version = models.OneToOneField(ReportCardVersion, on_delete=models.PROTECT, related_name='qr_token')
    token_hash = models.CharField(max_length=128, unique=True)
    token_version = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['report_version'], condition=Q(is_active=True), name='one_active_qr_per_report_version')]
        indexes = [models.Index(fields=['token_hash']), models.Index(fields=['is_active', 'expires_at'])]
    @staticmethod
    def hash_token(raw_token): return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    def clean(self):
        if self.is_active and self.report_version.report_card.status != ReportCard.Status.PUBLISHED:
            raise ValidationError('QR tokens may only be active for published reports.')
    def __str__(self): return f'QR for {self.report_version}'

class QRVerificationEvent(UUIDTimestampedModel):
    class Result(models.TextChoices):
        SUCCESS = 'success', 'Success'
        INVALID = 'invalid', 'Invalid'
        EXPIRED = 'expired', 'Expired'
        REVOKED = 'revoked', 'Revoked'
    qr_token = models.ForeignKey(QRToken, on_delete=models.PROTECT, null=True, blank=True, related_name='verification_events')
    attempted_token_hash = models.CharField(max_length=128, blank=True)
    result = models.CharField(max_length=20, choices=Result.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent_hash = models.CharField(max_length=128, blank=True)
    verified_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-verified_at']
        indexes = [models.Index(fields=['qr_token', '-verified_at']), models.Index(fields=['result', '-verified_at'])]
    def __str__(self): return f'{self.qr_token} - {self.result}'
