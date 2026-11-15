import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        PRINCIPAL = 'principal', 'Principal'
        TEACHER = 'teacher', 'Teacher'
        KINDERGARTEN_PRINCIPAL = 'kindergarten_principal', 'Kindergarten Principal'
        PRIMARY_PRINCIPAL = 'primary_principal', 'Primary Principal'
        STUDENT = 'student', 'Student'
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.STUDENT, db_index=True)
    class Meta: ordering = ['username']
    def __str__(self): return self.get_full_name() or self.username
    def retire(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at'])




