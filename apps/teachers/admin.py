from django.contrib import admin
from .models import TeacherProfile, TeachingAssignment, TeacherQualification, TeacherExperience, TeacherSalary

class TeachingAssignmentInline(admin.TabularInline):
    model = TeachingAssignment
    extra = 0
    fields = ('section_subject', 'starts_on', 'ends_on', 'is_lead', 'weekly_periods', 'is_active')
    autocomplete_fields = ('section_subject',)


class TeacherQualificationInline(admin.TabularInline):
    model = TeacherQualification
    extra = 0
    fields = ('qualification_type', 'field_of_study', 'institution', 'obtained_on', 'document')


class TeacherExperienceInline(admin.TabularInline):
    model = TeacherExperience
    extra = 0
    fields = ('organization', 'position', 'starts_on', 'ends_on', 'description')


class TeacherSalaryInline(admin.TabularInline):
    model = TeacherSalary
    extra = 0
    fields = ('amount', 'currency', 'frequency', 'effective_from', 'effective_to', 'is_current')

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_number', 'user', 'school', 'hired_on', 'is_active')
    list_filter = ('school', 'is_active', 'hired_on')
    search_fields = ('employee_number', 'user__username', 'user__first_name', 'user__last_name', 'user__email')
    ordering = ('school', 'employee_number')
    autocomplete_fields = ('school', 'user')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (TeachingAssignmentInline, TeacherQualificationInline, TeacherExperienceInline, TeacherSalaryInline)

@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'section_subject', 'is_lead', 'weekly_periods', 'is_active', 'starts_on', 'ends_on')
    list_filter = ('is_lead', 'is_active', 'teacher__school', 'section_subject__class_section__academic_year')
    search_fields = ('teacher__employee_number', 'teacher__user__username', 'section_subject__subject__name', 'section_subject__class_section__name')
    ordering = ('section_subject', '-is_lead', 'teacher')
    autocomplete_fields = ('teacher', 'section_subject')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(TeacherQualification)
class TeacherQualificationAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'qualification_type', 'field_of_study', 'institution', 'obtained_on')
    list_filter = ('teacher__school', 'qualification_type', 'obtained_on')
    search_fields = ('teacher__employee_number', 'teacher__user__last_name', 'qualification_type', 'field_of_study', 'institution')
    ordering = ('teacher', '-obtained_on')
    autocomplete_fields = ('teacher',)
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(TeacherExperience)
class TeacherExperienceAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'position', 'organization', 'starts_on', 'ends_on')
    list_filter = ('teacher__school', 'organization', 'starts_on')
    search_fields = ('teacher__employee_number', 'teacher__user__last_name', 'position', 'organization')
    ordering = ('teacher', '-starts_on')
    autocomplete_fields = ('teacher',)
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(TeacherSalary)
class TeacherSalaryAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'amount', 'currency', 'frequency', 'effective_from', 'effective_to', 'is_current')
    list_filter = ('teacher__school', 'currency', 'frequency', 'is_current')
    search_fields = ('teacher__employee_number', 'teacher__user__last_name', 'currency')
    ordering = ('teacher', '-effective_from')
    autocomplete_fields = ('teacher',)
    readonly_fields = ('id', 'created_at', 'updated_at')
