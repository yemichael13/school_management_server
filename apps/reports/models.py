from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from apps.core.models import UUIDTimestampedModel
from apps.academics.models import ReportPeriod, Subject
from apps.students.models import StudentEnrollment

class ReportCard(UUIDTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        APPROVED = 'approved', 'Approved'
        PUBLISHED = 'published', 'Published'
        REJECTED = 'rejected', 'Rejected'
    enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.PROTECT, related_name='report_cards')
    report_period = models.ForeignKey(ReportPeriod, on_delete=models.PROTECT, related_name='report_cards')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    current_version = models.OneToOneField('ReportCardVersion', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    class Meta:
        ordering = ['-updated_at', 'enrollment']
        constraints = [models.UniqueConstraint(fields=['enrollment', 'report_period'], name='one_report_card_per_enrollment_period')]
        indexes = [models.Index(fields=['status', '-updated_at']), models.Index(fields=['enrollment'])]
    def __str__(self): return f'{self.enrollment.student.student_id} / {self.report_period}'

class ReportCardVersion(UUIDTimestampedModel):
    report_card = models.ForeignKey(ReportCard, on_delete=models.PROTECT, related_name='versions')
    version_no = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    average = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    rank = models.PositiveIntegerField(null=True, blank=True)
    distinction = models.CharField(max_length=100, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    content_hash = models.CharField(max_length=128, unique=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='report_versions_generated')
    generated_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    teacher_comment = models.TextField(blank=True)
    principal_comment = models.TextField(blank=True)
    class Meta:
        ordering = ['report_card', '-version_no']
        constraints = [models.UniqueConstraint(fields=['report_card', 'version_no'], name='unique_report_card_version')]
        indexes = [models.Index(fields=['report_card', '-version_no']), models.Index(fields=['published_at'])]
    def clean(self):
        if self.rank is not None and self.rank < 1: raise ValidationError({'rank': 'Rank must be positive.'})
    def __str__(self): return f'{self.report_card} v{self.version_no}'

class ReportCardLine(UUIDTimestampedModel):
    report_version = models.ForeignKey(ReportCardVersion, on_delete=models.PROTECT, related_name='lines')
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='report_lines')
    subject_code = models.CharField(max_length=30)
    subject_name = models.CharField(max_length=150)
    numeric_mark = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    grade_code = models.CharField(max_length=20)
    distinction = models.CharField(max_length=100, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    class Meta:
        ordering = ['report_version', 'display_order', 'subject_name']
        constraints = [models.UniqueConstraint(fields=['report_version', 'subject'], name='one_report_line_per_subject')]
        indexes = [models.Index(fields=['report_version', 'display_order'])]
    def __str__(self): return f'{self.report_version} / {self.subject_name}: {self.grade_code}'

class ReportApproval(UUIDTimestampedModel):
    class Decision(models.TextChoices):
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    report_version = models.ForeignKey(ReportCardVersion, on_delete=models.PROTECT, related_name='approvals')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='report_approvals')
    decision = models.CharField(max_length=20, choices=Decision.choices)
    comment = models.TextField(blank=True)
    decided_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-decided_at']
        constraints = [models.UniqueConstraint(fields=['report_version', 'decision'], name='one_report_decision_type_per_version')]
    def __str__(self): return f'{self.report_version} - {self.decision}'

class ReportWorkflowEvent(UUIDTimestampedModel):
    report_card = models.ForeignKey(ReportCard, on_delete=models.PROTECT, related_name='workflow_events')
    report_version = models.ForeignKey(ReportCardVersion, on_delete=models.PROTECT, null=True, blank=True, related_name='workflow_events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='report_workflow_events')
    from_status = models.CharField(max_length=20, choices=ReportCard.Status.choices, blank=True)
    to_status = models.CharField(max_length=20, choices=ReportCard.Status.choices)
    comment = models.TextField(blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-occurred_at']
        indexes = [models.Index(fields=['report_card', '-occurred_at']), models.Index(fields=['actor', '-occurred_at'])]
    def __str__(self): return f'{self.report_card}: {self.from_status or "new"} -> {self.to_status}'
