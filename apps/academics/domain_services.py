from django.core.exceptions import ValidationError
from django.db import transaction

from .models import ClassSection, SectionSubject, Subject


class AcademicStructureService:
    @staticmethod
    @transaction.atomic
    def create_subject(*, school, **data):
        return Subject.objects.create(school=school, **data)

    @staticmethod
    @transaction.atomic
    def create_class_section(*, academic_year, grade_level, **data):
        return ClassSection.objects.create(academic_year=academic_year, grade_level=grade_level, **data)

    @staticmethod
    @transaction.atomic
    def add_subject_to_section(*, class_section, subject, grading_scheme, **data):
        if subject.school_id != class_section.academic_year.school_id:
            raise ValidationError('Subject and section must belong to the same school.')
        if grading_scheme.school_id != class_section.academic_year.school_id:
            raise ValidationError('Grading scheme and section must belong to the same school.')
        if grading_scheme.academic_year_id != class_section.academic_year_id:
            raise ValidationError('Grading scheme and section must belong to the same academic year.')
        if grading_scheme.school_level_id != class_section.grade_level.school_level_id:
            raise ValidationError('Grading scheme and section must use the same school level.')
        return SectionSubject.objects.create(
            class_section=class_section, subject=subject, grading_scheme=grading_scheme, **data
        )
