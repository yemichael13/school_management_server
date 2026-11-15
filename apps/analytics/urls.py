from django.urls import path

from .views import (AnalyticsDashboardView, AverageDistributionAnalyticsView,
                    PassFailAnalyticsView, StudentRankingAnalyticsView)

app_name = 'analytics'
urlpatterns = [
    path('dashboard/', AnalyticsDashboardView.as_view(), name='dashboard'),
    path('pass-fail/', PassFailAnalyticsView.as_view(), name='pass-fail'),
    path('average-distribution/', AverageDistributionAnalyticsView.as_view(), name='average-distribution'),
    path('students/', StudentRankingAnalyticsView.as_view(), name='students'),
]
