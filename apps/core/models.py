import uuid
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

class UUIDTimestampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class SchoolLevel(UUIDTimestampedModel):
    class Code(models.TextChoices):
        KINDERGARTEN = 'kindergarten', 'Kindergarten'
        PRIMARY = 'primary', 'Primary'
    code = models.CharField(max_length=20, choices=Code.choices, unique=True)
    name = models.CharField(max_length=100)
    display_order = models.PositiveSmallIntegerField(default=0)
    class Meta:
        ordering = ['display_order', 'name']
    def __str__(self): return self.name

class School(UUIDTimestampedModel):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='schools/logos/%Y/%m/', blank=True)
    stamp = models.ImageField(upload_to='schools/stamps/%Y/%m/', blank=True)
    principal_signature = models.ImageField(upload_to='schools/signatures/%Y/%m/', blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    class Meta: ordering = ['name']
    def __str__(self): return f'{self.code} - {self.name}'

class SchoolMembership(UUIDTimestampedModel):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        PRINCIPAL = 'principal', 'Principal'
        TEACHER = 'teacher', 'Teacher'
        STUDENT = 'student', 'Student'
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='school_memberships')
    role = models.CharField(max_length=20, choices=Role.choices)
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    class Meta:
        ordering = ['school', 'role', 'user']
        constraints = [
            models.UniqueConstraint(fields=['school', 'user'], name='unique_school_membership'),
            models.CheckConstraint(condition=Q(ends_on__isnull=True) | Q(starts_on__isnull=True) | Q(ends_on__gte=models.F('starts_on')), name='membership_dates_valid'),
        ]
        indexes = [models.Index(fields=['school', 'role', 'is_active'])]
    def __str__(self): return f'{self.user} - {self.school} ({self.role})'

class PrincipalScope(UUIDTimestampedModel):
    membership = models.ForeignKey(SchoolMembership, on_delete=models.CASCADE, related_name='principal_scopes')
    school_level = models.ForeignKey(SchoolLevel, on_delete=models.PROTECT, related_name='principal_scopes')
    class Meta:
        ordering = ['membership', 'school_level']
        constraints = [models.UniqueConstraint(fields=['membership', 'school_level'], name='unique_principal_scope')]
    def __str__(self): return f'{self.membership} / {self.school_level}'

class SchoolSetting(UUIDTimestampedModel):
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='settings')
    setting_key = models.CharField(max_length=100)
    version_no = models.PositiveIntegerField()
    value = models.JSONField(default=dict)
    is_current = models.BooleanField(default=True, db_index=True)
    class Meta:
        ordering = ['school', 'setting_key', '-version_no']
        constraints = [models.UniqueConstraint(fields=['school', 'setting_key', 'version_no'], name='unique_school_setting_version'), models.UniqueConstraint(fields=['school', 'setting_key'], condition=Q(is_current=True), name='one_current_school_setting')]
        indexes = [models.Index(fields=['school', 'setting_key', '-version_no'])]
    def __str__(self): return f'{self.school.code}: {self.setting_key} v{self.version_no}'
