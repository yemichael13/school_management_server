import sys
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassSection, GradeLevel, GradingRule, GradingScheme, ReportPeriod, SectionSubject, Subject
from apps.core.models import School, SchoolLevel
from apps.students.models import StudentEnrollment, StudentProfile
from apps.teachers.models import TeacherProfile, TeachingAssignment
from apps.marks.models import Mark
from apps.reports.models import ReportCard
from apps.reports.services import ReportGenerationService


class MarkManagementAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(code='DEG', name='Degnetu School')
        self.primary = SchoolLevel.objects.create(code='primary', name='Primary')
        self.kindergarten = SchoolLevel.objects.create(code='kindergarten', name='Kindergarten')
        self.year = AcademicYear.objects.create(school=self.school, code='2018-2019', start_date='2025-09-11', end_date='2026-07-07')
        self.primary_grade = GradeLevel.objects.create(school_level=self.primary, code='G1', name='Grade 1')
        self.kg_grade = GradeLevel.objects.create(school_level=self.kindergarten, code='KG1', name='KG 1')
        self.primary_section = ClassSection.objects.create(academic_year=self.year, grade_level=self.primary_grade, code='A', name='Primary A')
        self.kg_section = ClassSection.objects.create(academic_year=self.year, grade_level=self.kg_grade, code='A', name='Kindergarten A')
        self.primary_scheme = GradingScheme.objects.create(school=self.school, academic_year=self.year, school_level=self.primary, name='Primary Scheme')
        self.kg_scheme = GradingScheme.objects.create(school=self.school, academic_year=self.year, school_level=self.kindergarten, name='KG Scheme')
        for scheme in (self.primary_scheme, self.kg_scheme):
            GradingRule.objects.create(grading_scheme=scheme, min_mark=0, max_mark=49, grade_code='F')
            GradingRule.objects.create(grading_scheme=scheme, min_mark=50, max_mark=79, grade_code='B')
            GradingRule.objects.create(grading_scheme=scheme, min_mark=80, max_mark=100, grade_code='A', distinction='Excellent')
        self.math = Subject.objects.create(school=self.school, code='MATH', name='Mathematics')
        self.reading = Subject.objects.create(school=self.school, code='READ', name='Reading')
        self.primary_math = SectionSubject.objects.create(class_section=self.primary_section, subject=self.math, grading_scheme=self.primary_scheme)
        self.primary_reading = SectionSubject.objects.create(class_section=self.primary_section, subject=self.reading, grading_scheme=self.primary_scheme, display_order=1)
        self.kg_math = SectionSubject.objects.create(class_section=self.kg_section, subject=self.math, grading_scheme=self.kg_scheme)
        self.period = ReportPeriod.objects.create(academic_year=self.year, code='S1', name='Semester 1', sequence=1, starts_on='2025-09-11', ends_on='2026-01-31')
        self.student = StudentProfile.objects.create(school=self.school, student_id='ST-001', first_name='Student', admitted_on='2025-09-11')
        self.enrollment = StudentEnrollment.objects.create(student=self.student, academic_year=self.year, class_section=self.primary_section, enrollment_number='EN-001', started_on='2025-09-11')
        self.kg_student = StudentProfile.objects.create(school=self.school, student_id='ST-002', first_name='Kindergarten', admitted_on='2025-09-11')
        self.kg_enrollment = StudentEnrollment.objects.create(student=self.kg_student, academic_year=self.year, class_section=self.kg_section, enrollment_number='EN-002', started_on='2025-09-11')
        self.teacher = User.objects.create_user(username='teacher', password='StrongPass123!', role=User.Role.TEACHER)
        teacher_profile = TeacherProfile.objects.create(school=self.school, user=self.teacher, employee_number='T-001')
        TeachingAssignment.objects.create(teacher=teacher_profile, section_subject=self.primary_math)
        TeachingAssignment.objects.create(teacher=teacher_profile, section_subject=self.primary_reading)
        TeachingAssignment.objects.create(teacher=teacher_profile, section_subject=self.kg_math)
        self.principal = User.objects.create_user(username='principal', password='StrongPass123!', role=User.Role.PRINCIPAL)

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def test_primary_calculates_grade_total_average_and_distinction(self):
        self.auth(self.teacher)
        for section_subject, value in ((self.primary_math, 90), (self.primary_reading, 70)):
            response = self.client.post('/api/marks/marks/', {'enrollment': str(self.enrollment.id), 'section_subject': str(section_subject.id), 'value': value}, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report = self.client.post('/api/marks/reports/generate/', {'enrollment': str(self.enrollment.id), 'report_period': str(self.period.id)}, format='json')
        self.assertEqual(report.status_code, status.HTTP_201_CREATED)
        version = report.data['current_version']
        self.assertEqual(version['total'], '160.00')
        self.assertEqual(version['average'], '80.00')
        self.assertEqual(version['lines'][0]['grade_code'], 'A')
        self.assertIsNotNone(version['lines'][0]['numeric_mark'])
        self.assertEqual(version['lines'][0]['distinction'], 'Excellent')

    def test_kindergarten_stores_numeric_but_hides_it_in_report(self):
        self.auth(self.teacher)
        response = self.client.post('/api/marks/marks/', {'enrollment': str(self.kg_enrollment.id), 'section_subject': str(self.kg_math.id), 'value': 85}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report = self.client.post('/api/marks/reports/generate/', {'enrollment': str(self.kg_enrollment.id), 'report_period': str(self.period.id)}, format='json')
        self.assertEqual(report.status_code, status.HTTP_201_CREATED)
        line = report.data['current_version']['lines'][0]
        self.assertIsNone(line['numeric_mark'])
        self.assertEqual(line['grade_code'], 'A')
        self.assertEqual(Mark.objects.get(enrollment=self.kg_enrollment).value, 85)

    def test_submit_locks_marks_review_and_publish(self):
        self.auth(self.teacher)
        self.client.post('/api/marks/marks/', {'enrollment': str(self.enrollment.id), 'section_subject': str(self.primary_math.id), 'value': 85}, format='json')
        generated = self.client.post('/api/marks/reports/generate/', {'enrollment': str(self.enrollment.id), 'report_period': str(self.period.id)}, format='json')
        report_id = generated.data['id']
        submitted = self.client.post(f'/api/marks/reports/{report_id}/submit/')
        self.assertEqual(submitted.status_code, status.HTTP_200_OK)
        self.assertEqual(Mark.objects.get(enrollment=self.enrollment).status, Mark.Status.LOCKED)
        self.auth(self.principal)
        reviewed = self.client.post(f'/api/marks/reports/{report_id}/review/', {'decision': 'approved', 'comment': 'Reviewed'}, format='json')
        self.assertEqual(reviewed.status_code, status.HTTP_200_OK)
        published = self.client.post(f'/api/marks/reports/{report_id}/publish/')
        self.assertEqual(published.status_code, status.HTTP_200_OK)
        self.assertEqual(ReportCard.objects.get(pk=report_id).status, 'published')

    def test_mark_update_creates_revision_and_locked_mark_cannot_change(self):
        self.auth(self.teacher)
        created = self.client.post('/api/marks/marks/', {'enrollment': str(self.enrollment.id), 'section_subject': str(self.primary_math.id), 'value': 60}, format='json')
        mark_id = created.data['id']
        updated = self.client.patch(f'/api/marks/marks/{mark_id}/', {'value': 75}, format='json')
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(f'/api/marks/mark-revisions/?mark={mark_id}').data['count'], 2)
        self.client.post(f'/api/marks/marks/{mark_id}/lock/')
        blocked = self.client.patch(f'/api/marks/marks/{mark_id}/', {'value': 90}, format='json')
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)

    def test_primary_ranking_is_calculated_within_section(self):
        second_student = StudentProfile.objects.create(school=self.school, student_id='ST-003', first_name='Second', admitted_on='2025-09-11')
        second_enrollment = StudentEnrollment.objects.create(student=second_student, academic_year=self.year, class_section=self.primary_section, enrollment_number='EN-003', started_on='2025-09-11')
        self.auth(self.teacher)
        for enrollment, value in ((self.enrollment, 90), (second_enrollment, 70)):
            self.client.post('/api/marks/marks/', {'enrollment': str(enrollment.id), 'section_subject': str(self.primary_math.id), 'value': value}, format='json')
            self.client.post('/api/marks/reports/generate/', {'enrollment': str(enrollment.id), 'report_period': str(self.period.id)}, format='json')
        first = ReportCard.objects.get(enrollment=self.enrollment).current_version
        second = ReportCard.objects.get(enrollment=second_enrollment).current_version
        self.assertEqual(first.rank, 1)
        self.assertEqual(second.rank, 2)

    def test_primary_pdf_template_contains_primary_values_and_qr(self):
        self.auth(self.teacher)
        self.client.post('/api/marks/marks/', {'enrollment': str(self.enrollment.id), 'section_subject': str(self.primary_math.id), 'value': 85}, format='json')
        generated = self.client.post('/api/marks/reports/generate/', {'enrollment': str(self.enrollment.id), 'report_period': str(self.period.id), 'teacher_comment': 'Good progress'}, format='json')
        card = ReportCard.objects.get(pk=generated.data['id'])
        card.status = ReportCard.Status.PUBLISHED
        card.save(update_fields=['status', 'updated_at'])
        captured = {}

        class FakeHTML:
            def __init__(self, *, string, base_url):
                captured['html'] = string
            def write_pdf(self):
                return b'%PDF-primary'

        with patch.dict(sys.modules, {'weasyprint': SimpleNamespace(HTML=FakeHTML)}):
            pdf = ReportGenerationService.generate(report_card=card, save_document=False)
        self.assertTrue(pdf.startswith(b'%PDF'))
        self.assertIn('Primary Academic Report', captured['html'])
        self.assertIn('85.00', captured['html'])
        self.assertIn('Good progress', captured['html'])
        self.assertIn('data:image/png;base64', captured['html'])

    def test_kindergarten_pdf_hides_numeric_values(self):
        self.auth(self.teacher)
        self.client.post('/api/marks/marks/', {'enrollment': str(self.kg_enrollment.id), 'section_subject': str(self.kg_math.id), 'value': 85}, format='json')
        generated = self.client.post('/api/marks/reports/generate/', {'enrollment': str(self.kg_enrollment.id), 'report_period': str(self.period.id)}, format='json')
        card = ReportCard.objects.get(pk=generated.data['id'])
        card.status = ReportCard.Status.PUBLISHED
        card.save(update_fields=['status', 'updated_at'])
        captured = {}

        class FakeHTML:
            def __init__(self, *, string, base_url):
                captured['html'] = string
            def write_pdf(self):
                return b'%PDF-kindergarten'

        with patch.dict(sys.modules, {'weasyprint': SimpleNamespace(HTML=FakeHTML)}):
            ReportGenerationService.generate(report_card=card, save_document=False)
        self.assertIn('Kindergarten Progress Report', captured['html'])
        self.assertNotIn('85.00', captured['html'])
