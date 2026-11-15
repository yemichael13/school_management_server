from datetime import date
from io import BytesIO
from uuid import uuid4

from django.db import transaction
from django.http import HttpResponse
from openpyxl import Workbook, load_workbook

from apps.academics.models import AcademicYear, ClassSection, GradeLevel
from apps.promotions.models import Promotion
from .models import StudentEnrollment, StudentProfile, StudentTransfer


class StudentService:
    @staticmethod
    @transaction.atomic
    def register(*, validated_data):
        return StudentProfile.objects.create(**validated_data)

    @staticmethod
    @transaction.atomic
    def soft_delete(student):
        student.is_active = False
        student.save(update_fields=('is_active', 'updated_at'))
        if student.user_id:
            student.user.is_active = False
            student.user.save(update_fields=('is_active',))
        return student

    @staticmethod
    def history(student):
        return student.enrollments.select_related('academic_year', 'class_section', 'class_section__grade_level').order_by('-started_on')


class StudentLifecycleService:
    @staticmethod
    def _enrollment_number(student):
        return f'{student.student_id}-{uuid4().hex[:8].upper()}'

    @staticmethod
    def _validate_target(student, academic_year, class_section):
        if class_section.academic_year_id != academic_year.id:
            raise ValueError('The target section must belong to the target academic year.')
        if class_section.academic_year.school_id != student.school_id:
            raise ValueError('The target academic year must belong to the student school.')

    @staticmethod
    @transaction.atomic
    def promote(*, student, source_enrollment, academic_year, class_section, target_grade_level, effective_on, actor, reason=''):
        StudentLifecycleService._validate_target(student, academic_year, class_section)
        if class_section.grade_level_id != target_grade_level.id:
            raise ValueError('The target section must belong to the target grade level.')
        return Promotion.objects.create(
            source_enrollment=source_enrollment,
            target_academic_year=academic_year,
            target_grade_level=target_grade_level,
            target_class_section=class_section,
            proposed_by=actor,
            effective_on=effective_on,
            reason=reason,
        )

    @staticmethod
    @transaction.atomic
    def transfer(*, student, source_enrollment, academic_year, class_section, effective_on, reason):
        StudentLifecycleService._validate_target(student, academic_year, class_section)
        if source_enrollment.student_id != student.id:
            raise ValueError('The source enrollment does not belong to this student.')
        destination = StudentEnrollment.objects.create(
            student=student,
            academic_year=academic_year,
            class_section=class_section,
            enrollment_number=StudentLifecycleService._enrollment_number(student),
            started_on=effective_on,
            status=StudentEnrollment.Status.ACTIVE,
        )
        source_enrollment.status = StudentEnrollment.Status.TRANSFERRED
        source_enrollment.ended_on = effective_on
        source_enrollment.exit_reason = reason
        source_enrollment.save(update_fields=('status', 'ended_on', 'exit_reason', 'updated_at'))
        StudentTransfer.objects.create(source_enrollment=source_enrollment, destination_enrollment=destination, effective_on=effective_on, reason=reason)
        return destination

    @staticmethod
    @transaction.atomic
    def close_enrollment(*, student, enrollment, status, effective_on, reason):
        if enrollment.student_id != student.id:
            raise ValueError('The enrollment does not belong to this student.')
        if status not in (StudentEnrollment.Status.COMPLETED, StudentEnrollment.Status.WITHDRAWN):
            raise ValueError('Unsupported lifecycle status.')
        enrollment.status = status
        enrollment.ended_on = effective_on
        enrollment.exit_reason = reason
        enrollment.save(update_fields=('status', 'ended_on', 'exit_reason', 'updated_at'))
        return enrollment


class StudentExcelService:
    headers = ('student_id', 'first_name', 'middle_name', 'last_name', 'birth_date', 'sex', 'admitted_on')

    @staticmethod
    @transaction.atomic
    def import_students(*, workbook_file, school):
        workbook = load_workbook(workbook_file, read_only=True, data_only=True)
        sheet = workbook.active
        rows = sheet.iter_rows(values_only=True)
        header = tuple(str(value).strip() if value is not None else '' for value in next(rows, ()))
        missing = [field for field in StudentExcelService.headers if field not in header]
        if missing:
            raise ValueError(f'Missing required columns: {", ".join(missing)}')
        positions = {field: header.index(field) for field in StudentExcelService.headers}
        created = []
        errors = []
        for row_number, row in enumerate(rows, start=2):
            try:
                values = {field: row[index] for field, index in positions.items()}
                if not values['student_id'] or not values['first_name'] or not values['admitted_on']:
                    raise ValueError('student_id, first_name, and admitted_on are required')
                values['middle_name'] = values['middle_name'] or ''
                values['last_name'] = values['last_name'] or ''
                values['sex'] = values['sex'] or StudentProfile.Sex.UNDISCLOSED
                student = StudentProfile.objects.create(school=school, **values)
                created.append(student)
            except Exception as exc:
                errors.append({'row': row_number, 'error': str(exc)})
        return created, errors

    @staticmethod
    def export_students(queryset):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Students'
        sheet.append(StudentExcelService.headers)
        for student in queryset.order_by('student_id'):
            sheet.append((student.student_id, student.first_name, student.middle_name, student.last_name, student.birth_date, student.sex, student.admitted_on))
        output = BytesIO()
        workbook.save(output)
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="students.xlsx"'
        return response
