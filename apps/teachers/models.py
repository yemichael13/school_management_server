from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from apps.core.models import School, UUIDTimestampedModel
from apps.academics.models import SectionSubject

class TeacherProfile(UUIDTimestampedModel):
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='teachers')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='teacher_profile')
    employee_number = models.CharField(max_length=50)
    hired_on = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    class Meta:
        ordering = ['school', 'employee_number']
        constraints = [models.UniqueConstraint(fields=['school', 'employee_number'], name='unique_employee_per_school')]
    def __str__(self): return f'{self.employee_number} - {self.user.get_full_name() or self.user.username}'

class TeachingAssignment(UUIDTimestampedModel):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.PROTECT, related_name='teaching_assignments')
    section_subject = models.ForeignKey(SectionSubject, on_delete=models.PROTECT, related_name='teaching_assignments')
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)
    is_lead = models.BooleanField(default=False)
    weekly_periods = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True, db_index=True)
    class Meta:
        ordering = ['section_subject', '-is_lead', 'teacher']
        constraints = [models.CheckConstraint(condition=Q(ends_on__isnull=True) | Q(starts_on__isnull=True) | Q(ends_on__gte=models.F('starts_on')), name='teaching_dates_valid'), models.UniqueConstraint(fields=['section_subject'], condition=Q(is_active=True, is_lead=True), name='one_active_lead_teacher_per_subject')]
        indexes = [models.Index(fields=['teacher', 'is_active']), models.Index(fields=['section_subject', 'is_active'])]
    def __str__(self): return f'{self.teacher} / {self.section_subject}'

class TeacherQualification(UUIDTimestampedModel):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.PROTECT, related_name='qualifications')
    qualification_type = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=150, blank=True)
    institution = models.CharField(max_length=255)
    obtained_on = models.DateField(null=True, blank=True)
    document = models.FileField(upload_to='teachers/qualifications/%Y/%m/', blank=True)
    notes = models.TextField(blank=True)
    class Meta:
        ordering = ['teacher', '-obtained_on', 'qualification_type']
        indexes = [models.Index(fields=['teacher', 'qualification_type'])]
    def __str__(self): return f'{self.teacher} - {self.qualification_type}'

class TeacherExperience(UUIDTimestampedModel):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.PROTECT, related_name='experiences')
    organization = models.CharField(max_length=255)
    position = models.CharField(max_length=150)
    starts_on = models.DateField()
    ends_on = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    class Meta:
        ordering = ['teacher', '-starts_on']
        constraints = [models.CheckConstraint(condition=Q(ends_on__isnull=True) | Q(ends_on__gte=models.F('starts_on')), name='experience_dates_valid')]
    def __str__(self): return f'{self.teacher} - {self.position} at {self.organization}'

class TeacherSalary(UUIDTimestampedModel):
    class Frequency(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        ANNUAL = 'annual', 'Annual'
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.PROTECT, related_name='salary_history')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='ETB')
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.MONTHLY)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True, db_index=True)
    class Meta:
        ordering = ['teacher', '-effective_from']
        constraints = [models.CheckConstraint(condition=Q(effective_to__isnull=True) | Q(effective_to__gte=models.F('effective_from')), name='salary_dates_valid'), models.UniqueConstraint(fields=['teacher'], condition=Q(is_current=True), name='one_current_salary_per_teacher')]
        indexes = [models.Index(fields=['teacher', '-effective_from'])]
    def __str__(self): return f'{self.teacher} - {self.amount} {self.currency}'
