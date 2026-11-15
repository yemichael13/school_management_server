from rest_framework.routers import DefaultRouter

from .views import (AcademicYearViewSet, ClassSectionViewSet, GradeLevelViewSet, SectionSubjectViewSet,
                    GradeLevelViewSet, SchoolLevelViewSet, SubjectViewSet, SemesterViewSet)

router = DefaultRouter()
router.register('school-levels', SchoolLevelViewSet, basename='school-level')
router.register('academic-years', AcademicYearViewSet, basename='academic-year')
router.register('semesters', SemesterViewSet, basename='semester')
router.register('grade-levels', GradeLevelViewSet, basename='grade-level')
router.register('sections', ClassSectionViewSet, basename='section')
router.register('subjects', SubjectViewSet, basename='subject')
router.register('section-subjects', SectionSubjectViewSet, basename='section-subject')

app_name = 'academics'
urlpatterns = router.urls
