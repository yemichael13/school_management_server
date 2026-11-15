from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import CanViewAnalytics
from .serializers import AnalyticsFilterSerializer
from .services import AnalyticsService


class AnalyticsBaseView(APIView):
    permission_classes = (CanViewAnalytics,)

    def filters(self, request):
        serializer = AnalyticsFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data


class AnalyticsDashboardView(AnalyticsBaseView):
    def get(self, request):
        return Response(AnalyticsService.dashboard(**self.filters(request)))


class PassFailAnalyticsView(AnalyticsBaseView):
    def get(self, request):
        filters = self.filters(request)
        filters.pop('limit', None)
        return Response(AnalyticsService.pass_fail(reports=AnalyticsService.published_reports(**filters)))


class AverageDistributionAnalyticsView(AnalyticsBaseView):
    def get(self, request):
        filters = self.filters(request)
        filters.pop('limit', None)
        return Response(AnalyticsService.average_distribution(reports=AnalyticsService.published_reports(**filters)))


class StudentRankingAnalyticsView(AnalyticsBaseView):
    def get(self, request):
        filters = self.filters(request)
        limit = filters.pop('limit', 10)
        reports = AnalyticsService.published_reports(**filters)
        return Response({
            'top_students': AnalyticsService.students(reports=reports, limit=limit, descending=True),
            'lowest_students': AnalyticsService.students(reports=reports, limit=limit, descending=False),
        })
