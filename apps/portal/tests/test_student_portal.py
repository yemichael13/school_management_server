import sys
from datetime import time
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassSection, GradeLevel, GradingScheme, ReportPeriod, SectionSubject, Subject, TimetableEntry
from apps.core.models import School, SchoolLevel
from apps.reports.models import ReportCard, ReportCardLine, ReportCardVersion
from apps.students.models import StudentEnrollment, StudentProfile
from apps.teachers.models import TeacherProfile, TeachingAssignment


class StudentPortalTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(code='DEG', name='Degnetu School')
        level = SchoolLevel.objects.create(code='primary', name='Primary')
        year = AcademicYear.objects.create(school=self.school, code='2018-2019', start_date='2025-09-11', end_date='2026-07-07')
        grade = GradeLevel.objects.create(school_level=level, code='G1', name='Grade 1')
        section = ClassSection.objects.create(academic_year=year, grade_level=grade, code='A', name='Section A')
        subject = Subject.objects.create(school=self.school, code='MATH', name='Mathematics')
        scheme = GradingScheme.objects.create(school=self.school, academic_year=year, school_level=level, name='Primary')
        section_subject = SectionSubject.objects.create(class_section=section, subject=subject, grading_scheme=scheme)
        period = ReportPeriod.objects.create(academic_year=year, code='S1', name='Semester 1', sequence=1, starts_on='2025-09-11', ends_on='2026-01-31')
        self.user = User.objects.create_user(username='student', password='StrongPass123!', role=User.Role.STUDENT)
        student = StudentProfile.objects.create(school=self.school, user=self.user, student_id='PRIVATE-001', first_name='Portal', last_name='Student', admitted_on='2025-09-11')
        enrollment = StudentEnrollment.objects.create(student=student, academic_year=year, class_section=section, enrollment_number='EN-001', started_on='2025-09-11')
        card = ReportCard.objects.create(enrollment=enrollment, report_period=period, status=ReportCard.Status.PUBLISHED)
        version = ReportCardVersion.objects.create(report_card=card, version_no=1, total=85, average=85, rank=1, content_hash='portal-report-hash', published_at=timezone.now(), teacher_comment='Keep improving.')
        ReportCardLine.objects.create(report_version=version, subject=subject, subject_code='MATH', subject_name='Mathematics', numeric_mark=85, grade_code='A', display_order=0)
        card.current_version = version
        card.save(update_fields=['current_version', 'updated_at'])
        self.enrollment = enrollment
        self.section_subject = section_subject
        self.teacher_user = User.objects.create_user(username='teacher', password='StrongPass123!', role=User.Role.TEACHER)
        teacher = TeacherProfile.objects.create(school=self.school, user=self.teacher_user, employee_number='T-001')
        TeachingAssignment.objects.create(teacher=teacher, section_subject=section_subject)
        TimetableEntry.objects.create(class_section=section, section_subject=section_subject, weekday=TimetableEntry.Weekday.MONDAY, starts_at=time(8), ends_at=time(9), room='A-1')

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def test_student_can_view_only_published_reports_and_ranking(self):
        self.authenticate()
        reports = self.client.get('/api/portal/reports/')
        self.assertEqual(reports.status_code, status.HTTP_200_OK)
        self.assertEqual(reports.data['count'], 1)
        self.assertNotIn('student_id', reports.data['results'][0])
        ranking = self.client.get('/api/portal/ranking/')
        self.assertEqual(ranking.status_code, status.HTTP_200_OK)
        self.assertEqual(ranking.data[0]['rank'], 1)

    def test_student_can_view_own_timetable(self):
        self.authenticate()
        response = self.client.get('/api/portal/timetable/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['subject'], 'Mathematics')
        self.assertEqual(response.data[0]['teachers'], ['teacher'])

    def test_portal_is_read_only_and_rejects_non_students(self):
        self.authenticate()
        response = self.client.post('/api/portal/reports/', {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.client.force_authenticate(user=self.teacher_user)
        self.assertEqual(self.client.get('/api/portal/reports/').status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_download_published_pdf(self):
        self.authenticate()
        captured = {}

        class FakeHTML:
            def __init__(self, *, string, base_url):
                captured['html'] = string
            def write_pdf(self):
                return b'%PDF-portal'

        with patch.dict(sys.modules, {'weasyprint': SimpleNamespace(HTML=FakeHTML)}):
            response = self.client.get(f'/api/portal/reports/{self.enrollment.report_cards.first().id}/pdf/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(b'%PDF-portal', b''.join(response.streaming_content))
