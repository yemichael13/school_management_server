from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from apps.core.models import UUIDTimestampedModel
from apps.reports.models import ReportCardVersion

class ReportDocument(UUIDTimestampedModel):
    class Backend(models.TextChoices):
        LOCAL = 'local', 'Local'
        CLOUDINARY = 'cloudinary', 'Cloudinary'
    report_version = models.ForeignKey(ReportCardVersion, on_delete=models.PROTECT, related_name='documents')
    backend = models.CharField(max_length=20, choices=Backend.choices, default=Backend.LOCAL)
    object_key = models.CharField(max_length=500)
    checksum = models.CharField(max_length=128)
    file = models.FileField(upload_to='reports/%Y/%m/', blank=True, validators=[FileExtensionValidator(['pdf'])])
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='report_documents_generated')
    generated_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['report_version', '-generated_at']
        constraints = [models.UniqueConstraint(fields=['report_version', 'checksum'], name='unique_report_document_checksum')]
    def __str__(self): return f'{self.report_version} - {self.object_key}'
