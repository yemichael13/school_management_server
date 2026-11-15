from datetime import date
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import IntegerRangeField, RangeOperators
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from apps.core.models import School, SchoolLevel, UUIDTimestampedModel

class AcademicYear(UUIDTimestampedModel):
    class Status(models.TextChoices):
        PLANNED = 'planned', 'Planned'
        OPEN = 'open', 'Open'
        CLOSED = 'closed', 'Closed'
        ARCHIVED = 'archived', 'Archived'
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='academic_years')
    code = models.CharField(max_length=30)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED, db_index=True)
    is_current = models.BooleanField(default=False, db_index=True)
    class Meta:
        ordering = ['-start_date', 'code']
        constraints = [models.UniqueConstraint(fields=['school', 'code'], name='unique_school_academic_year'), models.CheckConstraint(condition=Q(end_date__gt=models.F('start_date')), name='academic_year_dates_valid'), models.UniqueConstraint(fields=['school'], condition=Q(is_current=True), name='one_current_academic_year')]
        indexes = [models.Index(fields=['school', '-start_date'])]
    def __str__(self): return f'{self.school.code} / {self.code}'

class Semester(UUIDTimestampedModel):
    class Status(models.TextChoices):
        PLANNED = 'planned', 'Planned'
        OPEN = 'open', 'Open'
        CLOSED = 'closed', 'Closed'

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='semesters')
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    sequence = models.PositiveSmallIntegerField()
    starts_on = models.DateField()
    ends_on = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED, db_index=True)
    is_current = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['academic_year', 'sequence']
        constraints = [
            models.UniqueConstraint(fields=['academic_year', 'code'], name='unique_semester_per_year'),
            models.UniqueConstraint(fields=['academic_year', 'sequence'], name='unique_semester_sequence'),
            models.CheckConstraint(condition=Q(ends_on__gte=models.F('starts_on')), name='semester_dates_valid'),
            models.UniqueConstraint(fields=['academic_year'], condition=Q(is_current=True), name='one_current_semester_per_year'),
        ]
        indexes = [models.Index(fields=['academic_year', 'status', 'sequence'])]

    def __str__(self): return f'{self.academic_year.code} - {self.name}'

class GradeLevel(UUIDTimestampedModel):
    school_level = models.ForeignKey(SchoolLevel, on_delete=models.PROTECT, related_name='grade_levels')
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    class Meta:
        ordering = ['school_level', 'display_order']
        constraints = [models.UniqueConstraint(fields=['school_level', 'code'], name='unique_grade_code_per_level')]
    def __str__(self): return self.name

class ClassSection(UUIDTimestampedModel):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='class_sections')
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.PROTECT, related_name='class_sections')
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True, db_index=True)
    class Meta:
        ordering = ['academic_year', 'grade_level__display_order', 'code']
        constraints = [models.UniqueConstraint(fields=['academic_year', 'grade_level', 'code'], name='unique_section_per_grade_year')]
        indexes = [models.Index(fields=['academic_year', 'grade_level'])]
    def __str__(self): return f'{self.grade_level.name} - {self.name}'

class Subject(UUIDTimestampedModel):
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='subjects')
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    class Meta:
        ordering = ['name']
        constraints = [models.UniqueConstraint(fields=['school', 'code'], name='unique_subject_code_per_school')]
    def __str__(self): return f'{self.code} - {self.name}'

class GradingScheme(UUIDTimestampedModel):
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='grading_schemes')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='grading_schemes')
    school_level = models.ForeignKey(SchoolLevel, on_delete=models.PROTECT, related_name='grading_schemes')
    name = models.CharField(max_length=100)
    passing_mark = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    calculates_total = models.BooleanField(default=True)
    calculates_average = models.BooleanField(default=True)
    calculates_rank = models.BooleanField(default=True)
    calculates_pass_fail = models.BooleanField(default=True)
    displays_numeric_marks = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True, db_index=True)
    class Meta:
        ordering = ['school', 'academic_year', 'school_level', 'name']
        constraints = [models.UniqueConstraint(fields=['school', 'academic_year', 'school_level'], name='unique_scheme_per_school_year_level'), models.CheckConstraint(condition=Q(passing_mark__isnull=True) | Q(passing_mark__gte=0, passing_mark__lte=100), name='passing_mark_valid')]
    def __str__(self): return f'{self.name} ({self.school_level.name})'

class GradingRule(UUIDTimestampedModel):
    grading_scheme = models.ForeignKey(GradingScheme, on_delete=models.PROTECT, related_name='rules')
    min_mark = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_mark = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    mark_range = IntegerRangeField(editable=False, null=True)
    grade_code = models.CharField(max_length=20)
    distinction = models.CharField(max_length=100, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    class Meta:
        ordering = ['grading_scheme', '-min_mark']
        constraints = [models.CheckConstraint(condition=Q(max_mark__gte=models.F('min_mark')), name='grading_rule_range_valid'), models.UniqueConstraint(fields=['grading_scheme', 'grade_code'], name='unique_grade_per_scheme'), ExclusionConstraint(expressions=[('grading_scheme', '='), ('mark_range', RangeOperators.OVERLAPS)], name='grading_rules_no_overlap')]
        indexes = [models.Index(fields=['grading_scheme', '-min_mark'])]
    def clean(self):
        if self.min_mark > self.max_mark: raise ValidationError({'max_mark': 'Maximum mark must be greater than or equal to minimum mark.'})
    def save(self, *args, **kwargs):
        self.mark_range = (int(self.min_mark), int(self.max_mark) + 1)
        return super().save(*args, **kwargs)
    def __str__(self): return f'{self.grade_code} ({self.min_mark}-{self.max_mark})'

class SectionSubject(UUIDTimestampedModel):
    class_section = models.ForeignKey(ClassSection, on_delete=models.PROTECT, related_name='section_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='section_subjects')
    grading_scheme = models.ForeignKey(GradingScheme, on_delete=models.PROTECT, related_name='section_subjects')
    display_order = models.PositiveSmallIntegerField(default=0)
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True, db_index=True)
    class Meta:
        ordering = ['class_section', 'display_order', 'subject__name']
        constraints = [models.UniqueConstraint(fields=['class_section', 'subject'], name='unique_subject_per_section'), models.UniqueConstraint(fields=['class_section', 'display_order'], name='unique_subject_order_per_section')]
        indexes = [models.Index(fields=['subject']), models.Index(fields=['class_section', 'display_order'])]
    def __str__(self): return f'{self.class_section} / {self.subject.name}'


class TimetableEntry(UUIDTimestampedModel):
    class Weekday(models.IntegerChoices):
        MONDAY = 1, 'Monday'
        TUESDAY = 2, 'Tuesday'
        WEDNESDAY = 3, 'Wednesday'
        THURSDAY = 4, 'Thursday'
        FRIDAY = 5, 'Friday'

    class_section = models.ForeignKey(ClassSection, on_delete=models.PROTECT, related_name='timetable_entries')
    section_subject = models.ForeignKey(SectionSubject, on_delete=models.PROTECT, related_name='timetable_entries')
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    starts_at = models.TimeField()
    ends_at = models.TimeField()
    room = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['class_section', 'weekday', 'starts_at']
        constraints = [
            models.UniqueConstraint(fields=['class_section', 'weekday', 'starts_at'], name='unique_timetable_slot_per_section'),
            models.CheckConstraint(condition=Q(ends_at__gt=models.F('starts_at')), name='timetable_times_valid'),
        ]
        indexes = [models.Index(fields=['class_section', 'weekday', 'starts_at'])]

    def __str__(self):
        return f'{self.class_section} / {self.section_subject.subject.name} / {self.get_weekday_display()}'

class ReportPeriod(UUIDTimestampedModel):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='report_periods')
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    sequence = models.PositiveSmallIntegerField()
    starts_on = models.DateField()
    ends_on = models.DateField()
    is_published = models.BooleanField(default=False, db_index=True)
    class Meta:
        ordering = ['academic_year', 'sequence']
        constraints = [models.UniqueConstraint(fields=['academic_year', 'code'], name='unique_report_period_per_year'), models.UniqueConstraint(fields=['academic_year', 'sequence'], name='unique_report_period_sequence'), models.CheckConstraint(condition=Q(ends_on__gte=models.F('starts_on')), name='report_period_dates_valid')]
    def __str__(self): return f'{self.academic_year.code} - {self.name}'


