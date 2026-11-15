from io import BytesIO

from django.http import FileResponse
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports.services import ReportGenerationService

from .permissions import IsStudentUser
from .serializers import PortalReportSerializer, PortalTimetableSerializer
from .services import StudentPortalService


class StudentReportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PortalReportSerializer
    permission_classes = (IsStudentUser,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('updated_at', 'report_period__sequence')
    ordering = ('-updated_at',)

    def get_queryset(self):
        return StudentPortalService.reports_for(self.request.user)

    @staticmethod
    def _pdf_response(request, report):
        pdf = ReportGenerationService.generate(report_card=report, actor=request.user)
        return FileResponse(BytesIO(pdf), content_type='application/pdf', filename=f'report-card-{report.id}.pdf')

    @action(detail=True, methods=('get',))
    def pdf(self, request, pk=None):
        return self._pdf_response(request, self.get_object())


class StudentRankingView(APIView):
    permission_classes = (IsStudentUser,)

    def get(self, request):
        rows = []
        for item in StudentPortalService.rankings_for(request.user):
            rows.append({
                'report_period_id': str(item['report_period__id']),
                'report_period': item['report_period__name'],
                'version': item['current_version__version_no'],
                'rank': item['current_version__rank'],
                'average': item['current_version__average'],
                'total': item['current_version__total'],
            })
        return Response(rows)


class StudentTimetableView(APIView):
    permission_classes = (IsStudentUser,)

    def get(self, request):
        timetable = StudentPortalService.timetable_for(request.user)
        return Response(PortalTimetableSerializer(timetable, many=True).data)
