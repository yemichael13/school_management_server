from rest_framework.routers import DefaultRouter

from .views import MarkRevisionViewSet, MarkViewSet, ReportCardViewSet

router = DefaultRouter()
router.register('marks', MarkViewSet, basename='mark')
router.register('mark-revisions', MarkRevisionViewSet, basename='mark-revision')
router.register('reports', ReportCardViewSet, basename='mark-report')

app_name = 'marks'
urlpatterns = router.urls
