from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, viewsets

from .domain_services import AcademicStructureService
from .models import AcademicYear, ClassSection, GradeLevel, SectionSubject, Semester, Subject
from .permissions import IsAcademicManagerOrReadOnly
from .serializers import (AcademicYearSerializer, ClassSectionSerializer, GradeLevelSerializer,
                          SchoolLevelSerializer, SectionSubjectSerializer, SemesterSerializer, SubjectSerializer)
from apps.core.models import SchoolLevel


class AcademicManagementViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAcademicManagerOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    page_size = 25


class SchoolLevelViewSet(AcademicManagementViewSet):
    queryset = SchoolLevel.objects.all()
    serializer_class = SchoolLevelSerializer
    search_fields = ('code', 'name')
    ordering_fields = ('display_order', 'name', 'code')
    ordering = ('display_order', 'name')
    filterset_fields = ('code',)


class AcademicYearViewSet(AcademicManagementViewSet):
    queryset = AcademicYear.objects.select_related('school')
    serializer_class = AcademicYearSerializer
    search_fields = ('code', 'school__name', 'school__code')
    ordering_fields = ('start_date', 'end_date', 'code', 'status')
    ordering = ('-start_date', 'code')
    filterset_fields = ('school', 'status', 'is_current')


class SemesterViewSet(AcademicManagementViewSet):
    queryset = Semester.objects.select_related('academic_year', 'academic_year__school')
    serializer_class = SemesterSerializer
    search_fields = ('code', 'name', 'academic_year__code')
    ordering_fields = ('sequence', 'starts_on', 'ends_on', 'status')
    ordering = ('academic_year', 'sequence')
    filterset_fields = ('academic_year', 'status', 'is_current')


class GradeLevelViewSet(AcademicManagementViewSet):
    queryset = GradeLevel.objects.select_related('school_level')
    serializer_class = GradeLevelSerializer
    search_fields = ('code', 'name', 'school_level__name')
    ordering_fields = ('display_order', 'code', 'name')
    ordering = ('school_level', 'display_order')
    filterset_fields = ('school_level', 'is_active')


class ClassSectionViewSet(AcademicManagementViewSet):
    queryset = ClassSection.objects.select_related('academic_year', 'grade_level', 'grade_level__school_level')
    serializer_class = ClassSectionSerializer
    search_fields = ('code', 'name', 'academic_year__code', 'grade_level__name')
    ordering_fields = ('code', 'name', 'capacity', 'is_active')
    ordering = ('academic_year', 'grade_level__display_order', 'code')
    filterset_fields = ('academic_year', 'grade_level', 'is_active')

    def perform_create(self, serializer):
        serializer.instance = AcademicStructureService.create_class_section(**serializer.validated_data)


class SubjectViewSet(AcademicManagementViewSet):
    queryset = Subject.objects.select_related('school')
    serializer_class = SubjectSerializer
    search_fields = ('code', 'name', 'description', 'school__name', 'school__code')
    ordering_fields = ('code', 'name', 'is_active')
    ordering = ('name',)
    filterset_fields = ('school', 'is_active')

    def perform_create(self, serializer):
        serializer.instance = AcademicStructureService.create_subject(**serializer.validated_data)


class SectionSubjectViewSet(AcademicManagementViewSet):
    queryset = SectionSubject.objects.select_related('class_section', 'subject', 'grading_scheme')
    serializer_class = SectionSubjectSerializer
    search_fields = ('class_section__name', 'class_section__code', 'subject__name', 'subject__code')
    ordering_fields = ('display_order', 'is_required', 'is_active')
    ordering = ('class_section', 'display_order', 'subject__name')
    filterset_fields = ('class_section', 'subject', 'grading_scheme', 'is_required', 'is_active')

    def perform_create(self, serializer):
        try:
            serializer.instance = AcademicStructureService.add_subject_to_section(**serializer.validated_data)
        except ValidationError as exc:
            raise serializers.ValidationError({'detail': exc.messages})
