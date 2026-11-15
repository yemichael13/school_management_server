from django.conf import settings
from django.db import models
from apps.core.models import UUIDTimestampedModel

class Notification(UUIDTimestampedModel):
    class Type(models.TextChoices):
        RESULTS_PUBLISHED = 'results_published', 'Results Published'
        REPORT_READY = 'report_ready', 'Report Ready'
        REPORT = 'report', 'Report'
        APPROVAL = 'approval', 'Approval'
        PROMOTION = 'promotion', 'Promotion'
        SYSTEM = 'system', 'System'
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=Type.choices, default=Type.SYSTEM)
    title = models.CharField(max_length=255)
    message = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    dedupe_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['recipient', 'read_at', '-created_at'])]
    def mark_read(self):
        if self.read_at is None:
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save(update_fields=['read_at', 'updated_at'])
    def __str__(self): return f'{self.recipient} - {self.title}'
