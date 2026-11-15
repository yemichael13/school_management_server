from datetime import date
from io import BytesIO

from django.test import TestCase
from openpyxl import Workbook, load_workbook
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassSection, GradeLevel
from apps.core.models import School, SchoolLevel
from apps.students.models import StudentEnrollment, StudentProfile


class StudentManagementAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username='student-admin', password='StrongPass123!', role=User.Role.ADMIN)
        self.school = School.objects.create(code='DEG', name='Degnetu School')
        self.level = SchoolLevel.objects.create(code='primary', name='Primary')
        self.grade_one = GradeLevel.objects.create(school_level=self.level, code='G1', name='Grade 1', display_order=1)
        self.grade_two = GradeLevel.objects.create(school_level=self.level, code='G2', name='Grade 2', display_order=2)
        self.year = AcademicYear.objects.create(school=self.school, code='2018-2019', start_date='2025-09-11', end_date='2026-07-07')
        self.next_year = AcademicYear.objects.create(school=self.school, code='2019-2020', start_date='2026-09-11', end_date='2027-07-07')
        self.section_one = ClassSection.objects.create(academic_year=self.year, grade_level=self.grade_one, code='A', name='Section A')
        self.section_two = ClassSection.objects.create(academic_year=self.next_year, grade_level=self.grade_two, code='A', name='Section A')
        self.client.force_authenticate(user=self.admin)

    def register(self):
        return self.client.post('/api/students/students/', {
            'school': str(self.school.id), 'student_id': 'STU-001', 'first_name': 'Mekdes',
            'last_name': 'Bekele', 'sex': 'female', 'admitted_on': '2025-09-11',
        }, format='json')

    def test_registration_edit_and_soft_delete_preserve_record(self):
        response = self.register()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        student_id = response.data['id']
        edited = self.client.patch(f'/api/students/students/{student_id}/', {'last_name': 'Tesfaye'}, format='json')
        self.assertEqual(edited.status_code, status.HTTP_200_OK)
        deleted = self.client.delete(f'/api/students/students/{student_id}/')
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(StudentProfile.objects.get(pk=student_id).is_active)

    def test_transfer_creates_destination_and_preserves_source_history(self):
        student = StudentProfile.objects.create(school=self.school, student_id='STU-002', first_name='Abel', admitted_on='2025-09-11')
        source = StudentEnrollment.objects.create(student=student, academic_year=self.year, class_section=self.section_one, enrollment_number='ENR-001', started_on='2025-09-11')
        response = self.client.post(f'/api/students/students/{student.id}/transfer/', {
            'academic_year': str(self.next_year.id), 'class_section': str(self.section_two.id), 'effective_on': '2026-01-10', 'reason': 'Family relocation',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        source.refresh_from_db()
        self.assertEqual(source.status, StudentEnrollment.Status.TRANSFERRED)
        self.assertEqual(student.enrollments.filter(status=StudentEnrollment.Status.ACTIVE).count(), 1)

    def test_promotion_graduation_withdrawal_and_history(self):
        student = StudentProfile.objects.create(school=self.school, student_id='STU-003', first_name='Hana', admitted_on='2025-09-11')
        StudentEnrollment.objects.create(student=student, academic_year=self.year, class_section=self.section_one, enrollment_number='ENR-002', started_on='2025-09-11')
        promotion = self.client.post(f'/api/students/students/{student.id}/promote/', {
            'academic_year': str(self.next_year.id), 'class_section': str(self.section_two.id), 'target_grade_level': str(self.grade_two.id), 'effective_on': '2026-09-11',
        }, format='json')
        self.assertEqual(promotion.status_code, status.HTTP_201_CREATED)
        history = self.client.get(f'/api/students/students/{student.id}/history/')
        self.assertEqual(history.status_code, status.HTTP_200_OK)
        graduation = self.client.post(f'/api/students/students/{student.id}/graduate/', {'effective_on': '2026-07-07', 'reason': 'Completed primary'}, format='json')
        self.assertEqual(graduation.status_code, status.HTTP_200_OK)

    def test_excel_import_and_export(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(('student_id', 'first_name', 'middle_name', 'last_name', 'birth_date', 'sex', 'admitted_on'))
        sheet.append(('STU-004', 'Liya', '', 'Kebede', date(2015, 1, 1), 'female', date(2025, 9, 11)))
        payload = BytesIO()
        workbook.save(payload)
        upload = SimpleUploadedFile('students.xlsx', payload.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response = self.client.post('/api/students/students/import/', {'school': str(self.school.id), 'file': upload}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['created'], 1)
        export = self.client.get(f'/api/students/students/export/?school={self.school.id}')
        self.assertEqual(export.status_code, status.HTTP_200_OK)
        exported = load_workbook(BytesIO(export.content), read_only=True)
        self.assertEqual(exported.active.max_row, 2)

    def test_teacher_role_is_allowed_but_student_is_not(self):
        teacher = User.objects.create_user(username='teacher', password='StrongPass123!', role=User.Role.TEACHER)
        self.client.force_authenticate(user=teacher)
        self.assertEqual(self.client.get('/api/students/students/').status_code, status.HTTP_200_OK)
        student_user = User.objects.create_user(username='student', password='StrongPass123!', role=User.Role.STUDENT)
        self.client.force_authenticate(user=student_user)
        self.assertEqual(self.client.get('/api/students/students/').status_code, status.HTTP_403_FORBIDDEN)
