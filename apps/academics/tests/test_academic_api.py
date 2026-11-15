from datetime import date

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassSection, GradeLevel, GradingScheme, SectionSubject, Semester, Subject
from apps.academics.services import gregorian_to_ethiopian
from apps.core.models import School, SchoolLevel


class AcademicManagementAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(code='DEG', name='Degnetu School')
        self.kindergarten = SchoolLevel.objects.create(code='kindergarten', name='Kindergarten', display_order=1)
        self.primary = SchoolLevel.objects.create(code='primary', name='Primary', display_order=2)
        self.grade = GradeLevel.objects.create(school_level=self.primary, code='G1', name='Grade 1', display_order=1)
        self.admin = User.objects.create_user(username='admin', password='StrongPass123!', role=User.Role.ADMIN)
        self.teacher = User.objects.create_user(username='teacher', password='StrongPass123!', role=User.Role.TEACHER)

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_ethiopian_conversion_known_new_year(self):
        self.assertEqual(gregorian_to_ethiopian(date(2011, 9, 11))['iso'], '2004-01-01')

    def test_manager_can_create_academic_year_and_semester(self):
        self.authenticate(self.admin)
        year_response = self.client.post('/api/academics/academic-years/', {
            'school': str(self.school.id), 'code': '2018-2019', 'start_date': '2025-09-11',
            'end_date': '2026-07-07', 'status': 'planned', 'is_current': True,
        }, format='json')
        self.assertEqual(year_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(year_response.data['start_date_ethiopian']['iso'], '2018-01-01')
        year_id = year_response.data['id']
        semester_response = self.client.post('/api/academics/semesters/', {
            'academic_year': year_id, 'code': 'S1', 'name': 'Semester 1', 'sequence': 1,
            'starts_on': '2025-09-11', 'ends_on': '2026-01-31', 'status': 'open', 'is_current': True,
        }, format='json')
        self.assertEqual(semester_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(semester_response.data['starts_on_ethiopian']['year'], 2018)

    def test_teacher_can_read_but_cannot_mutate_structure(self):
        self.authenticate(self.teacher)
        response = self.client.get('/api/academics/grade-levels/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post('/api/academics/grade-levels/', {
            'school_level': str(self.primary.id), 'code': 'G2', 'name': 'Grade 2', 'display_order': 2,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_date_ranges_are_rejected(self):
        self.authenticate(self.admin)
        response = self.client.post('/api/academics/academic-years/', {
            'school': str(self.school.id), 'code': 'bad', 'start_date': '2026-01-01', 'end_date': '2025-01-01',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_section_creation_and_filtering(self):
        year = AcademicYear.objects.create(school=self.school, code='2018-2019', start_date='2025-09-11', end_date='2026-07-07')
        ClassSection.objects.create(academic_year=year, grade_level=self.grade, code='A', name='Section A')
        self.authenticate(self.admin)
        response = self.client.get(f'/api/academics/sections/?academic_year={year.id}&search=Section')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_subjects_are_assigned_per_section_independently(self):
        year = AcademicYear.objects.create(school=self.school, code='2018-2019', start_date='2025-09-11', end_date='2026-07-07')
        section_a = ClassSection.objects.create(academic_year=year, grade_level=self.grade, code='A', name='Section A')
        section_b = ClassSection.objects.create(academic_year=year, grade_level=self.grade, code='B', name='Section B')
        scheme = GradingScheme.objects.create(school=self.school, academic_year=year, school_level=self.primary, name='Primary')
        math = Subject.objects.create(school=self.school, code='MATH', name='Mathematics')
        english = Subject.objects.create(school=self.school, code='ENG', name='English')
        self.authenticate(self.admin)
        first = self.client.post('/api/academics/section-subjects/', {
            'class_section': str(section_a.id), 'subject': str(math.id), 'grading_scheme': str(scheme.id),
        }, format='json')
        second = self.client.post('/api/academics/section-subjects/', {
            'class_section': str(section_b.id), 'subject': str(english.id), 'grading_scheme': str(scheme.id),
        }, format='json')
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SectionSubject.objects.filter(class_section=section_a).count(), 1)
        self.assertEqual(SectionSubject.objects.filter(class_section=section_b).count(), 1)
        self.assertEqual(SectionSubject.objects.get(class_section=section_a).subject, math)
        self.assertEqual(SectionSubject.objects.get(class_section=section_b).subject, english)

    def test_section_subject_rejects_cross_school_subject(self):
        year = AcademicYear.objects.create(school=self.school, code='2018-2019', start_date='2025-09-11', end_date='2026-07-07')
        section = ClassSection.objects.create(academic_year=year, grade_level=self.grade, code='A', name='Section A')
        scheme = GradingScheme.objects.create(school=self.school, academic_year=year, school_level=self.primary, name='Primary')
        other_school = School.objects.create(code='OTH', name='Other School')
        foreign_subject = Subject.objects.create(school=other_school, code='SCI', name='Science')
        self.authenticate(self.admin)
        response = self.client.post('/api/academics/section-subjects/', {
            'class_section': str(section.id), 'subject': str(foreign_subject.id), 'grading_scheme': str(scheme.id),
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
