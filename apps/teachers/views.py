from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import TeacherExperience, TeacherProfile, TeacherQualification, TeacherSalary, TeachingAssignment
from .permissions import IsTeacherManagerOrReadOnly
from .serializers import (TeacherExperienceSerializer, TeacherProfileSerializer, TeacherQualificationSerializer,
                          TeacherSalarySerializer, TeachingAssignmentSerializer)
from .services import TeacherAssignmentService


class TeacherBaseViewSet(viewsets.ModelViewSet):
    permission_classes = (IsTeacherManagerOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)


class TeacherProfileViewSet(TeacherBaseViewSet):
    queryset = TeacherProfile.objects.select_related('school', 'user').prefetch_related('teaching_assignments')
    serializer_class = TeacherProfileSerializer
    search_fields = ('employee_number', 'user__username', 'user__first_name', 'user__last_name', 'user__email')
    ordering_fields = ('employee_number', 'hired_on', 'is_active')
    ordering = ('school', 'employee_number')
    filterset_fields = ('school', 'is_active')

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self.request.user, 'role', None) == 'teacher':
            return queryset.filter(user=self.request.user)
        return queryset

    @action(detail=True, methods=('get',))
    def workload(self, request, pk=None):
        return Response(TeacherAssignmentService.workload(self.get_object()))


class TeachingAssignmentViewSet(TeacherBaseViewSet):
    queryset = TeachingAssignment.objects.select_related('teacher__user', 'section_subject__subject', 'section_subject__class_section__academic_year')
    serializer_class = TeachingAssignmentSerializer
    search_fields = ('teacher__employee_number', 'teacher__user__username', 'section_subject__subject__name', 'section_subject__class_section__name')
    ordering_fields = ('starts_on', 'ends_on', 'weekly_periods', 'is_active')
    ordering = ('section_subject', '-is_lead', 'teacher')
    filterset_fields = ('teacher', 'section_subject', 'is_lead', 'is_active')

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self.request.user, 'role', None) == 'teacher':
            queryset = queryset.filter(teacher__user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        assignment = TeacherAssignmentService.assign(**serializer.validated_data)
        serializer.instance = assignment


class TeacherQualificationViewSet(TeacherBaseViewSet):
    queryset = TeacherQualification.objects.select_related('teacher__user')
    serializer_class = TeacherQualificationSerializer
    search_fields = ('teacher__employee_number', 'qualification_type', 'field_of_study', 'institution')
    ordering = ('teacher', '-obtained_on')
    filterset_fields = ('teacher', 'qualification_type')

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(teacher__user=self.request.user) if getattr(self.request.user, 'role', None) == 'teacher' else queryset


class TeacherExperienceViewSet(TeacherBaseViewSet):
    queryset = TeacherExperience.objects.select_related('teacher__user')
    serializer_class = TeacherExperienceSerializer
    search_fields = ('teacher__employee_number', 'position', 'organization')
    ordering = ('teacher', '-starts_on')
    filterset_fields = ('teacher', 'organization')

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(teacher__user=self.request.user) if getattr(self.request.user, 'role', None) == 'teacher' else queryset


class TeacherSalaryViewSet(TeacherBaseViewSet):
    queryset = TeacherSalary.objects.select_related('teacher__user')
    serializer_class = TeacherSalarySerializer
    search_fields = ('teacher__employee_number', 'currency')
    ordering = ('teacher', '-effective_from')
    filterset_fields = ('teacher', 'currency', 'frequency', 'is_current')

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(teacher__user=self.request.user) if getattr(self.request.user, 'role', None) == 'teacher' else queryset

