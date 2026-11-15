from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Sum

from .models import TeachingAssignment


class TeacherAssignmentService:
    @staticmethod
    @transaction.atomic
    def assign(*, teacher, section_subject, **data):
        if section_subject.class_section.academic_year.school_id != teacher.school_id:
            raise ValidationError('Teacher and class section must belong to the same school.')
        return TeachingAssignment.objects.create(teacher=teacher, section_subject=section_subject, **data)

    @staticmethod
    def workload(teacher):
        assignments = teacher.teaching_assignments.filter(is_active=True)
        summary = assignments.aggregate(total_periods=Sum('weekly_periods'), assignment_count=Count('id'))
        return {
            'teacher': teacher.id,
            'assignment_count': summary['assignment_count'] or 0,
            'subject_count': assignments.values('section_subject__subject').distinct().count(),
            'class_count': assignments.values('section_subject__class_section').distinct().count(),
            'total_weekly_periods': summary['total_periods'] or 0,
        }

