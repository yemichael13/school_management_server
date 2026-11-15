from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response

from apps.core.models import School
from .models import StudentEnrollment, StudentProfile
from .permissions import IsStudentManager
from .serializers import EnrollmentActionSerializer, EnrollmentSummarySerializer, ExcelImportSerializer, LifecycleActionSerializer, PromotionRequestSerializer, StudentHistorySerializer, StudentProfileSerializer
from .services import StudentExcelService, StudentLifecycleService, StudentService


class StudentViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStudentManager,)
    serializer_class = StudentProfileSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('student_id', 'first_name', 'middle_name', 'last_name', 'school__name')
    ordering_fields = ('student_id', 'first_name', 'last_name', 'admitted_on', 'created_at')
    ordering = ('last_name', 'first_name', 'student_id')

    def get_queryset(self):
        queryset = StudentProfile.objects.select_related('school', 'user').prefetch_related('enrollments')
        school = self.request.query_params.get('school')
        active = self.request.query_params.get('is_active')
        if school:
            queryset = queryset.filter(school_id=school)
        if active in ('true', 'false'):
            queryset = queryset.filter(is_active=(active == 'true'))
        return queryset

    def perform_create(self, serializer):
        serializer.instance = StudentService.register(validated_data=serializer.validated_data)

    def perform_destroy(self, instance):
        StudentService.soft_delete(instance)

    @action(detail=True, methods=('get',), url_path='history')
    def history(self, request, pk=None):
        student = self.get_object()
        return Response(StudentHistorySerializer(StudentService.history(student), many=True).data)

    @action(detail=True, methods=('post',), url_path='promote')
    def promote(self, request, pk=None):
        student = self.get_object()
        serializer = PromotionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            promotion = StudentLifecycleService.promote(student=student, source_enrollment=self._source_enrollment(student), actor=request.user, **serializer.validated_data)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'id': str(promotion.id), 'status': promotion.status}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=('post',), url_path='transfer')
    def transfer(self, request, pk=None):
        student = self.get_object()
        serializer = EnrollmentActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            destination = StudentLifecycleService.transfer(student=student, source_enrollment=self._source_enrollment(student), **serializer.validated_data)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(EnrollmentSummarySerializer(destination).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=('post',), url_path='graduate')
    def graduate(self, request, pk=None):
        return self._close(request, StudentEnrollment.Status.COMPLETED)

    @action(detail=True, methods=('post',), url_path='withdraw')
    def withdraw(self, request, pk=None):
        return self._close(request, StudentEnrollment.Status.WITHDRAWN)

    @action(detail=False, methods=('post',), url_path='import', parser_classes=(MultiPartParser, FormParser))
    def import_students(self, request):
        serializer = ExcelImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        school = get_object_or_404(School, pk=serializer.validated_data['school'])
        try:
            created, errors = StudentExcelService.import_students(workbook_file=serializer.validated_data['file'], school=school)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'created': len(created), 'errors': errors}, status=status.HTTP_201_CREATED if not errors else status.HTTP_207_MULTI_STATUS)

    @action(detail=False, methods=('get',), url_path='export')
    def export_students(self, request):
        return StudentExcelService.export_students(self.filter_queryset(self.get_queryset()))

    def _source_enrollment(self, student):
        enrollment = student.enrollments.filter(status=StudentEnrollment.Status.ACTIVE).order_by('-started_on').first()
        if not enrollment:
            raise ValueError('The student has no active enrollment.')
        return enrollment

    def _close(self, request, lifecycle_status):
        student = self.get_object()
        serializer = LifecycleActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            enrollment = StudentLifecycleService.close_enrollment(student=student, enrollment=self._source_enrollment(student), status=lifecycle_status, **serializer.validated_data)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(EnrollmentSummarySerializer(enrollment).data)
