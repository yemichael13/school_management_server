from django.contrib import admin
from .models import Mark, MarkRevision

@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ('student_id_display', 'section_subject', 'value', 'status', 'entered_by', 'finalized_at', 'updated_at')
    list_filter = ('status', 'section_subject__class_section__academic_year', 'section_subject__subject', 'finalized_at', 'section_subject__class_section__grade_level')
    search_fields = ('enrollment__student__student_id', 'enrollment__student__first_name', 'enrollment__student__last_name', 'section_subject__subject__name', 'entered_by__username')
    ordering = ('enrollment', 'section_subject__display_order')
    autocomplete_fields = ('enrollment', 'section_subject', 'entered_by', 'finalized_by')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 100
    inlines = ()
    @admin.display(description='Student', ordering='enrollment__student__student_id')
    def student_id_display(self, obj): return obj.enrollment.student.student_id


@admin.register(MarkRevision)
class MarkRevisionAdmin(admin.ModelAdmin):
    list_display = ('mark', 'version_no', 'value', 'changed_by', 'reason', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('mark__enrollment__student__student_id', 'changed_by__username', 'reason')
    ordering = ('mark', '-version_no')
    autocomplete_fields = ('mark', 'changed_by')
    readonly_fields = ('id', 'created_at', 'updated_at')
