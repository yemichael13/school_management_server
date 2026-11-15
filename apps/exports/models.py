from django.conf import settings
from django.db import models
from apps.core.models import School, UUIDTimestampedModel

class ExportJob(UUIDTimestampedModel):
    class Type(models.TextChoices):
        MARKS = 'marks', 'Marks'
        REPORTS = 'reports', 'Reports'
        STUDENTS = 'students', 'Students'
    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='export_jobs')
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='export_jobs')
    export_type = models.CharField(max_length=20, choices=Type.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED, db_index=True)
    filters = models.JSONField(default=dict, blank=True)
    object_key = models.CharField(max_length=500, blank=True)
    checksum = models.CharField(max_length=128, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['school', 'status', '-created_at']), models.Index(fields=['requested_by', '-created_at'])]
    def __str__(self): return f'{self.export_type} export ({self.status})'
