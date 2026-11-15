from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassSection, GradeLevel, GradingScheme, SectionSubject, Subject
from apps.core.models import School, SchoolLevel
from apps.teachers.models import TeacherProfile


class TeacherManagementAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(code='DEG', name='Degnetu School')
        self.primary = SchoolLevel.objects.create(code='primary', name='Primary')
        self.grade = GradeLevel.objects.create(school_level=self.primary, code='G1', name='Grade 1')
        self.year = AcademicYear.objects.create(school=self.school, code='2018-2019', start_date='2025-09-11', end_date='2026-07-07')
        self.section_a = ClassSection.objects.create(academic_year=self.year, grade_level=self.grade, code='A', name='Section A')
        self.section_b = ClassSection.objects.create(academic_year=self.year, grade_level=self.grade, code='B', name='Section B')
        self.subject = Subject.objects.create(school=self.school, code='MATH', name='Mathematics')
        self.subject_two = Subject.objects.create(school=self.school, code='ENG', name='English')
        self.scheme = GradingScheme.objects.create(school=self.school, academic_year=self.year, school_level=self.primary, name='Primary')
        self.section_subject_a = SectionSubject.objects.create(class_section=self.section_a, subject=self.subject, grading_scheme=self.scheme)
        self.section_subject_b = SectionSubject.objects.create(class_section=self.section_b, subject=self.subject_two, grading_scheme=self.scheme)
        self.admin = User.objects.create_user(username='admin', password='StrongPass123!', role=User.Role.ADMIN)
        self.teacher_user = User.objects.create_user(username='teacher', first_name='Ayele', password='StrongPass123!', role=User.Role.TEACHER)
        self.teacher = TeacherProfile.objects.create(school=self.school, user=self.teacher_user, employee_number='T-001')

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def test_manager_can_create_profile_details_and_assignment(self):
        self.auth(self.admin)
        qualification = self.client.post('/api/teachers/qualifications/', {
            'teacher': str(self.teacher.id), 'qualification_type': 'Degree', 'field_of_study': 'Mathematics', 'institution': 'University',
        }, format='json')
        self.assertEqual(qualification.status_code, status.HTTP_201_CREATED)
        experience = self.client.post('/api/teachers/experiences/', {
            'teacher': str(self.teacher.id), 'organization': 'School', 'position': 'Teacher', 'starts_on': '2020-09-01',
        }, format='json')
        self.assertEqual(experience.status_code, status.HTTP_201_CREATED)
        salary = self.client.post('/api/teachers/salaries/', {
            'teacher': str(self.teacher.id), 'amount': '12000.00', 'currency': 'ETB', 'frequency': 'monthly', 'effective_from': '2025-09-01',
        }, format='json')
        self.assertEqual(salary.status_code, status.HTTP_201_CREATED)
        assignment = self.client.post('/api/teachers/assignments/', {
            'teacher': str(self.teacher.id), 'section_subject': str(self.section_subject_a.id), 'weekly_periods': 5, 'is_lead': True,
        }, format='json')
        self.assertEqual(assignment.status_code, status.HTTP_201_CREATED)

    def test_many_to_many_assignments_and_workload(self):
        self.auth(self.admin)
        for section_subject, periods in ((self.section_subject_a, 5), (self.section_subject_b, 3)):
            response = self.client.post('/api/teachers/assignments/', {
                'teacher': str(self.teacher.id), 'section_subject': str(section_subject.id), 'weekly_periods': periods,
            }, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(f'/api/teachers/teachers/{self.teacher.id}/workload/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assignment_count'], 2)
        self.assertEqual(response.data['subject_count'], 2)
        self.assertEqual(response.data['class_count'], 2)
        self.assertEqual(response.data['total_weekly_periods'], 8)

    def test_teacher_can_read_own_records_but_cannot_mutate(self):
        self.auth(self.teacher_user)
        response = self.client.get('/api/teachers/teachers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        response = self.client.post('/api/teachers/assignments/', {
            'teacher': str(self.teacher.id), 'section_subject': str(self.section_subject_a.id), 'weekly_periods': 4,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_experience_dates_are_rejected(self):
        self.auth(self.admin)
        response = self.client.post('/api/teachers/experiences/', {
            'teacher': str(self.teacher.id), 'organization': 'School', 'position': 'Teacher', 'starts_on': '2025-01-01', 'ends_on': '2024-01-01',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

