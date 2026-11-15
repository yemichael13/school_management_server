from rest_framework.routers import DefaultRouter

from .views import (TeacherExperienceViewSet, TeacherProfileViewSet, TeacherQualificationViewSet,
                    TeacherSalaryViewSet, TeachingAssignmentViewSet)

router = DefaultRouter()
router.register('teachers', TeacherProfileViewSet, basename='teacher')
router.register('assignments', TeachingAssignmentViewSet, basename='teaching-assignment')
router.register('qualifications', TeacherQualificationViewSet, basename='teacher-qualification')
router.register('experiences', TeacherExperienceViewSet, basename='teacher-experience')
router.register('salaries', TeacherSalaryViewSet, basename='teacher-salary')

app_name = 'teachers'
urlpatterns = router.urls
