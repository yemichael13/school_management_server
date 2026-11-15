from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import StudentRankingView, StudentReportViewSet, StudentTimetableView

router = DefaultRouter()
router.register('reports', StudentReportViewSet, basename='student-portal-report')

app_name = 'portal'
urlpatterns = [
    path('', include(router.urls)),
    path('ranking/', StudentRankingView.as_view(), name='ranking'),
    path('timetable/', StudentTimetableView.as_view(), name='timetable'),
]
