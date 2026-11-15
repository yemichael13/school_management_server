from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from apps.core.models import School, UUIDTimestampedModel
from apps.academics.models import AcademicYear, ClassSection

class StudentProfile(UUIDTimestampedModel):
    class Sex(models.TextChoices):
        FEMALE = 'female', 'Female'
        MALE = 'male', 'Male'
        OTHER = 'other', 'Other'
        UNDISCLOSED = 'undisclosed', 'Undisclosed'
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='students')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='student_profile', null=True, blank=True)
    student_id = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=20, choices=Sex.choices, default=Sex.UNDISCLOSED)
    admitted_on = models.DateField()
    photo = models.ImageField(upload_to='students/%Y/%m/', blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    class Meta:
        ordering = ['last_name', 'first_name', 'student_id']
        constraints = [models.UniqueConstraint(fields=['school', 'student_id'], name='unique_student_id_per_school')]
        indexes = [models.Index(fields=['school', 'last_name', 'first_name'])]
    @property
    def full_name(self): return ' '.join(filter(None, [self.first_name, self.middle_name, self.last_name]))
    def __str__(self): return f'{self.student_id} - {self.full_name}'

class Guardian(UUIDTimestampedModel):
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='guardians')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    class Meta: ordering = ['last_name', 'first_name']
    def __str__(self): return ' '.join(filter(None, [self.first_name, self.last_name]))

class StudentGuardian(UUIDTimestampedModel):
    class Relationship(models.TextChoices):
        MOTHER = 'mother', 'Mother'
        FATHER = 'father', 'Father'
        GUARDIAN = 'guardian', 'Guardian'
        OTHER = 'other', 'Other'
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name='guardian_links')
    guardian = models.ForeignKey(Guardian, on_delete=models.PROTECT, related_name='student_links')
    relationship = models.CharField(max_length=20, choices=Relationship.choices)
    is_primary = models.BooleanField(default=False)
    notification_consent = models.BooleanField(default=True)
    class Meta:
        ordering = ['-is_primary', 'guardian']
        constraints = [models.UniqueConstraint(fields=['student', 'guardian', 'relationship'], name='unique_student_guardian_relationship'), models.UniqueConstraint(fields=['student'], condition=Q(is_primary=True), name='one_primary_guardian_per_student')]
    def __str__(self): return f'{self.student} / {self.guardian} ({self.relationship})'

class StudentEnrollment(UUIDTimestampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        TRANSFERRED = 'transferred', 'Transferred'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
        PROMOTED = 'promoted', 'Promoted'
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name='enrollments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='student_enrollments')
    class_section = models.ForeignKey(ClassSection, on_delete=models.PROTECT, related_name='student_enrollments')
    enrollment_number = models.CharField(max_length=60, unique=True)
    started_on = models.DateField()
    ended_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    exit_reason = models.CharField(max_length=255, blank=True)
    class Meta:
        ordering = ['student', '-started_on']
        constraints = [models.CheckConstraint(condition=Q(ended_on__isnull=True) | Q(ended_on__gte=models.F('started_on')), name='enrollment_dates_valid')]
        indexes = [models.Index(fields=['student', 'academic_year', '-started_on']), models.Index(fields=['class_section', 'status'])]
    def __str__(self): return f'{self.student.student_id} / {self.academic_year.code} / {self.class_section}'

class StudentTransfer(UUIDTimestampedModel):
    source_enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.PROTECT, related_name='outgoing_transfers')
    destination_enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.PROTECT, related_name='incoming_transfers')
    effective_on = models.DateField()
    reason = models.CharField(max_length=255)
    class Meta:
        ordering = ['-effective_on']
        constraints = [models.CheckConstraint(condition=~Q(source_enrollment=models.F('destination_enrollment')), name='transfer_source_differs_destination')]
    def __str__(self): return f'{self.source_enrollment} -> {self.destination_enrollment}'
