from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from apps.core.models import UUIDTimestampedModel
from apps.academics.models import AcademicYear, ClassSection, GradeLevel
from apps.students.models import StudentEnrollment

class Promotion(UUIDTimestampedModel):
    class Status(models.TextChoices):
        PROPOSED = 'proposed', 'Proposed'
        TEACHER_FINALIZED = 'teacher_finalized', 'Teacher Finalized'
        PRINCIPAL_APPROVED = 'principal_approved', 'Principal Approved'
        ADMIN_REVIEWED = 'admin_reviewed', 'Admin Reviewed'
        COMPLETED = 'completed', 'Completed'
        REJECTED = 'rejected', 'Rejected'
    source_enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.PROTECT, related_name='promotions_from')
    target_academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='promotion_targets')
    target_grade_level = models.ForeignKey(GradeLevel, on_delete=models.PROTECT, related_name='promotion_targets')
    target_class_section = models.ForeignKey(ClassSection, on_delete=models.PROTECT, null=True, blank=True, related_name='promotion_targets')
    target_enrollment = models.OneToOneField(StudentEnrollment, on_delete=models.PROTECT, null=True, blank=True, related_name='promotion_source')
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PROPOSED, db_index=True)
    proposed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='promotions_proposed')
    effective_on = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    proposed_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ['-proposed_at']
        constraints = [models.CheckConstraint(condition=Q(target_enrollment__isnull=True) | Q(status='completed'), name='completed_promotion_has_target')]
        indexes = [models.Index(fields=['source_enrollment']), models.Index(fields=['status', '-proposed_at'])]
    def clean(self):
        if self.target_class_section_id and self.target_class_section.grade_level_id != self.target_grade_level_id:
            raise ValidationError('Target section must belong to the target grade.')
    def __str__(self): return f'{self.source_enrollment.student.student_id} promotion to {self.target_grade_level.name}'

class PromotionApproval(UUIDTimestampedModel):
    class Role(models.TextChoices):
        TEACHER = 'teacher', 'Teacher'
        PRINCIPAL = 'principal', 'Principal'
        ADMIN = 'admin', 'Admin'
    class Decision(models.TextChoices):
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    promotion = models.ForeignKey(Promotion, on_delete=models.PROTECT, related_name='approvals')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='promotion_approvals')
    role = models.CharField(max_length=20, choices=Role.choices)
    decision = models.CharField(max_length=20, choices=Decision.choices)
    comment = models.TextField(blank=True)
    decided_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['promotion', 'role', '-decided_at']
        constraints = [models.UniqueConstraint(fields=['promotion', 'role'], condition=Q(decision='approved'), name='one_approved_promotion_role')]
    def __str__(self): return f'{self.promotion} / {self.role} / {self.decision}'


