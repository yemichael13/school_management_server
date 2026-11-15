from django.conf import settings
from django.db import models
from apps.core.models import School, UUIDTimestampedModel

class AuditLog(UUIDTimestampedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    school = models.ForeignKey(School, on_delete=models.PROTECT, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.UUIDField(null=True, blank=True)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    request_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['school', '-created_at']), models.Index(fields=['entity_type', 'entity_id']), models.Index(fields=['actor', '-created_at']), models.Index(fields=['action', '-created_at'])]
    def __str__(self): return f'{self.action} {self.entity_type}:{self.entity_id}'
