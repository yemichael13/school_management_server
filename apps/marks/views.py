from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.reports.models import ReportCard

from .models import Mark, MarkRevision
from .permissions import MarkPermission, ReportPermission
from .serializers import MarkRevisionSerializer, MarkSerializer, ReportCardSerializer, ReportReviewSerializer
from .services import MarkService, ReportWorkflowService
from apps.reports.services import ReportGenerationService


class MarkViewSet(viewsets.ModelViewSet):
    queryset = Mark.objects.select_related('enrollment__student', 'section_subject__subject', 'entered_by').prefetch_related('revisions')
    serializer_class = MarkSerializer
    permission_classes = (MarkPermission,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('enrollment__student__student_id', 'enrollment__student__first_name', 'enrollment__student__last_name', 'section_subject__subject__name')
    ordering_fields = ('value', 'status', 'updated_at')
    ordering = ('enrollment', 'section_subject__display_order')
    filterset_fields = ('enrollment', 'section_subject', 'status')

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self.request.user, 'role', None) == 'teacher':
            return queryset.filter(section_subject__teaching_assignments__teacher__user=self.request.user).distinct()
        return queryset

    def perform_create(self, serializer):
        try:
            serializer.instance = MarkService.enter(actor=self.request.user, **serializer.validated_data)
        except Exception as exc:
            if hasattr(exc, 'messages'):
                raise serializers.ValidationError({'detail': exc.messages})
            raise

    def perform_update(self, serializer):
        try:
            serializer.instance = MarkService.enter(mark=self.get_object(), actor=self.request.user, **serializer.validated_data)
        except Exception as exc:
            if hasattr(exc, 'messages'):
                raise serializers.ValidationError({'detail': exc.messages})
            raise

    @action(detail=True, methods=('post',))
    def submit(self, request, pk=None):
        try:
            return Response(MarkSerializer(MarkService.submit(mark=self.get_object(), actor=request.user)).data)
        except Exception as exc:
            raise serializers.ValidationError({'detail': getattr(exc, 'messages', [str(exc)])})

    @action(detail=True, methods=('post',))
    def lock(self, request, pk=None):
        try:
            return Response(MarkSerializer(MarkService.lock(mark=self.get_object(), actor=request.user)).data)
        except Exception as exc:
            raise serializers.ValidationError({'detail': getattr(exc, 'messages', [str(exc)])})

    @action(detail=True, methods=('post',))
    def unlock(self, request, pk=None):
        if request.user.role not in ('admin', 'principal', 'kindergarten_principal', 'primary_principal'):
            return Response({'detail': 'Only managers can unlock marks.'}, status=403)
        try:
            return Response(MarkSerializer(MarkService.unlock(mark=self.get_object(), actor=request.user)).data)
        except Exception as exc:
            raise serializers.ValidationError({'detail': getattr(exc, 'messages', [str(exc)])})


class MarkRevisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MarkRevision.objects.select_related('mark', 'changed_by')
    serializer_class = MarkRevisionSerializer
    permission_classes = (MarkPermission,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_fields = ('mark', 'changed_by')
    ordering = ('mark', '-version_no')


class ReportCardViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReportCard.objects.select_related('enrollment__student', 'report_period', 'current_version').prefetch_related('current_version__lines')
    serializer_class = ReportCardSerializer
    permission_classes = (ReportPermission,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('enrollment__student__student_id', 'enrollment__student__first_name', 'enrollment__student__last_name')
    filterset_fields = ('enrollment', 'report_period', 'status')
    ordering = ('-updated_at', 'enrollment')

    @action(detail=False, methods=('post',), url_path='generate')
    def generate(self, request):
        enrollment_id = request.data.get('enrollment')
        period_id = request.data.get('report_period')
        from apps.students.models import StudentEnrollment
        from apps.academics.models import ReportPeriod
        try:
            enrollment = StudentEnrollment.objects.get(pk=enrollment_id)
            period = ReportPeriod.objects.get(pk=period_id)
            card, _ = ReportWorkflowService.build_version(
                enrollment=enrollment, report_period=period, actor=request.user,
                teacher_comment=request.data.get('teacher_comment', ''),
                principal_comment=request.data.get('principal_comment', ''),
            )
            return Response(ReportCardSerializer(card, context={'request': request}).data, status=201)
        except Exception as exc:
            raise serializers.ValidationError({'detail': getattr(exc, 'messages', [str(exc)])})

    @action(detail=True, methods=('post',))
    def submit(self, request, pk=None):
        return self._workflow(request, 'submit')

    @action(detail=True, methods=('post',))
    def review(self, request, pk=None):
        data = ReportReviewSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            card = ReportWorkflowService.review(report_card=self.get_object(), actor=request.user, **data.validated_data)
            return Response(ReportCardSerializer(card).data)
        except Exception as exc:
            raise serializers.ValidationError({'detail': getattr(exc, 'messages', [str(exc)])})

    @action(detail=True, methods=('post',))
    def publish(self, request, pk=None):
        return self._workflow(request, 'publish')

    @action(detail=True, methods=('get',))
    def pdf(self, request, pk=None):
        card = self.get_object()
        if card.status != ReportCard.Status.PUBLISHED and request.user.role not in ('admin', 'principal', 'kindergarten_principal', 'primary_principal'):
            return Response({'detail': 'Only published report cards are available as PDFs.'}, status=403)
        pdf = ReportGenerationService.generate(report_card=card, actor=request.user)
        return FileResponse(__import__('io').BytesIO(pdf), content_type='application/pdf', filename=f'{card.enrollment.student.student_id}-report.pdf')

    def _workflow(self, request, operation):
        try:
            card = getattr(ReportWorkflowService, operation)(report_card=self.get_object(), actor=request.user)
            return Response(ReportCardSerializer(card).data)
        except Exception as exc:
            raise serializers.ValidationError({'detail': getattr(exc, 'messages', [str(exc)])})
