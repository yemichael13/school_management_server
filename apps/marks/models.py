from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from apps.core.models import UUIDTimestampedModel
from apps.students.models import StudentEnrollment
from apps.academics.models import SectionSubject
from apps.teachers.models import TeacherProfile

class Mark(UUIDTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        LOCKED = 'locked', 'Locked'
    enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.PROTECT, related_name='marks')
    section_subject = models.ForeignKey(SectionSubject, on_delete=models.PROTECT, related_name='marks')
    value = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='marks_entered')
    finalized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='marks_finalized')
    finalized_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    locked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='marks_locked')
    locked_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ['enrollment', 'section_subject__display_order']
        constraints = [models.UniqueConstraint(fields=['enrollment', 'section_subject'], name='one_mark_per_enrollment_subject')]
        indexes = [models.Index(fields=['enrollment']), models.Index(fields=['section_subject']), models.Index(fields=['status', 'updated_at'])]
    def clean(self):
        if self.enrollment_id and self.section_subject_id:
            if self.enrollment.class_section_id != self.section_subject.class_section_id:
                raise ValidationError('The mark enrollment and section subject must belong to the same class section.')
    def __str__(self): return f'{self.enrollment.student.student_id} / {self.section_subject.subject.name}: {self.value}'


class MarkRevision(UUIDTimestampedModel):
    mark = models.ForeignKey(Mark, on_delete=models.PROTECT, related_name='revisions')
    version_no = models.PositiveIntegerField()
    value = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='mark_revisions')
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['mark', '-version_no']
        constraints = [models.UniqueConstraint(fields=['mark', 'version_no'], name='unique_mark_revision')]
        indexes = [models.Index(fields=['mark', '-version_no'])]

    def __str__(self): return f'{self.mark} v{self.version_no}'
