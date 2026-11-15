from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.academics.models import AcademicYear, ClassSection, GradeLevel, ReportPeriod
from apps.core.models import School, SchoolLevel
from apps.reports.models import ReportCard, ReportCardVersion
from apps.students.models import StudentEnrollment, StudentProfile

from apps.qr.models import QRToken, QRVerificationEvent
from apps.qr.services import QRVerificationService


class QRVerificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        school = School.objects.create(code='DEG', name='Degnetu School')
        level = SchoolLevel.objects.create(code='primary', name='Primary')
        year = AcademicYear.objects.create(school=school, code='2018-2019', start_date='2025-09-11', end_date='2026-07-07')
        grade = GradeLevel.objects.create(school_level=level, code='G1', name='Grade 1')
        section = ClassSection.objects.create(academic_year=year, grade_level=grade, code='A', name='Section A')
        period = ReportPeriod.objects.create(academic_year=year, code='S1', name='Semester 1', sequence=1, starts_on='2025-09-11', ends_on='2026-01-31')
        student = StudentProfile.objects.create(school=school, student_id='PRIVATE-001', first_name='Public', last_name='Student', admitted_on='2025-09-11')
        enrollment = StudentEnrollment.objects.create(student=student, academic_year=year, class_section=section, enrollment_number='EN-001', started_on='2025-09-11')
        card = ReportCard.objects.create(enrollment=enrollment, report_period=period, status=ReportCard.Status.PUBLISHED)
        version = ReportCardVersion.objects.create(report_card=card, version_no=1, average=82, content_hash='qr-test-hash-1', published_at=timezone.now())
        card.current_version = version
        card.save(update_fields=['current_version', 'updated_at'])
        self.raw_token, self.qr_token = QRVerificationService.generate_token(report_version=version)

    def test_public_verification_returns_authentic_without_student_id(self):
        response = self.client.get('/api/qr/verify/', {'token': self.raw_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['authentic'])
        self.assertEqual(response.data['status'], 'authentic')
        self.assertNotIn('student_id', response.data['report'])
        self.assertNotIn('PRIVATE-001', response.content.decode())
        self.assertEqual(QRVerificationEvent.objects.filter(result=QRVerificationEvent.Result.SUCCESS).count(), 1)

    def test_invalid_token_is_safe_and_recorded(self):
        response = self.client.get('/api/qr/verify/', {'token': 'invalid-token'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['authentic'])
        self.assertEqual(response.data['status'], 'invalid')
        self.assertIsNone(response.data['report'])
        event = QRVerificationEvent.objects.latest('created_at')
        self.assertEqual(event.result, QRVerificationEvent.Result.INVALID)
        self.assertIsNone(event.qr_token)
        self.assertTrue(event.attempted_token_hash)

    def test_revoked_and_expired_tokens_are_not_authentic(self):
        self.qr_token.revoked_at = timezone.now()
        self.qr_token.save(update_fields=['revoked_at', 'updated_at'])
        revoked = self.client.get('/api/qr/verify/', {'token': self.raw_token})
        self.assertEqual(revoked.data['status'], 'revoked')
        self.qr_token.revoked_at = None
        self.qr_token.expires_at = timezone.now() - timedelta(minutes=1)
        self.qr_token.save(update_fields=['revoked_at', 'expires_at', 'updated_at'])
        expired = self.client.get('/api/qr/verify/', {'token': self.raw_token})
        self.assertEqual(expired.data['status'], 'expired')
