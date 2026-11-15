from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassSection, GradeLevel, ReportPeriod, Subject
from apps.analytics.services import AnalyticsService
from apps.core.models import School, SchoolLevel
from apps.reports.models import ReportCard, ReportCardLine, ReportCardVersion
from apps.students.models import StudentEnrollment, StudentProfile


class AnalyticsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(code='DEG', name='Degnetu School')
        level = SchoolLevel.objects.create(code='primary', name='Primary')
        year = AcademicYear.objects.create(school=self.school, code='2018-2019', start_date='2025-09-11', end_date='2026-07-07')
        grade = GradeLevel.objects.create(school_level=level, code='G1', name='Grade 1')
        section = ClassSection.objects.create(academic_year=year, grade_level=grade, code='A', name='Section A')
        self.period = ReportPeriod.objects.create(academic_year=year, code='S1', name='Semester 1', sequence=1, starts_on='2025-09-11', ends_on='2026-01-31')
        self.subject = Subject.objects.create(school=self.school, code='MATH', name='Mathematics')
        self.admin = User.objects.create_user(username='analytics-admin', password='StrongPass123!', role=User.Role.ADMIN)
        self.teacher = User.objects.create_user(username='analytics-teacher', password='StrongPass123!', role=User.Role.TEACHER)
        for index, (average, passed) in enumerate(((95, True), (75, True), (45, False)), start=1):
            student = StudentProfile.objects.create(school=self.school, student_id=f'ST-{index}', first_name=f'Student {index}', admitted_on='2025-09-11')
            enrollment = StudentEnrollment.objects.create(student=student, academic_year=year, class_section=section, enrollment_number=f'EN-{index}', started_on='2025-09-11')
            card = ReportCard.objects.create(enrollment=enrollment, report_period=self.period, status=ReportCard.Status.PUBLISHED)
            version = ReportCardVersion.objects.create(report_card=card, version_no=1, total=average, average=average, rank=index, passed=passed, content_hash=f'analytics-hash-{index}', published_at=timezone.now())
            ReportCardLine.objects.create(report_version=version, subject=self.subject, subject_code='MATH', subject_name='Mathematics', numeric_mark=average, grade_code='A' if passed else 'F')
            card.current_version = version
            card.save(update_fields=['current_version', 'updated_at'])

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_dashboard_returns_react_ready_chart_payload(self):
        self.authenticate(self.admin)
        response = self.client.get('/api/analytics/dashboard/', {'school': str(self.school.id), 'report_period': str(self.period.id), 'limit': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pass_fail']['passed'], 2)
        self.assertEqual(response.data['pass_fail']['failed'], 1)
        self.assertEqual(response.data['pass_fail']['pass_rate'], Decimal('66.67'))
        self.assertEqual(response.data['pass_fail']['fail_rate'], Decimal('33.33'))
        self.assertEqual(response.data['average_distribution'][0]['count'], 1)
        self.assertEqual(len(response.data['top_students']), 2)
        self.assertEqual(response.data['top_students'][0]['average'], 95.0)
        self.assertEqual(len(response.data['lowest_students']), 2)
        self.assertEqual(response.data['lowest_students'][0]['average'], 45.0)

    def test_focused_chart_endpoints_and_filters(self):
        self.authenticate(self.teacher)
        response = self.client.get('/api/analytics/pass-fail/', {'class_section': 'not-a-uuid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get('/api/analytics/students/', {'subject': str(self.subject.id), 'limit': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['top_students']), 1)
        self.assertEqual(response.data['top_students'][0]['average'], 95.0)

    def test_students_cannot_access_analytics(self):
        student = User.objects.create_user(username='portal-student', password='StrongPass123!', role=User.Role.STUDENT)
        self.authenticate(student)
        self.assertEqual(self.client.get('/api/analytics/dashboard/').status_code, status.HTTP_403_FORBIDDEN)

    def test_service_excludes_unpublished_reports(self):
        reports = AnalyticsService.published_reports(school=self.school.id)
        self.assertEqual(reports.count(), 3)
