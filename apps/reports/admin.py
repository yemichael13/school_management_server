from django.contrib import admin
from .models import ReportCard, ReportCardVersion, ReportCardLine, ReportApproval, ReportWorkflowEvent

class ReportCardVersionInline(admin.TabularInline):
    model = ReportCardVersion
    extra = 0
    fields = ('version_no', 'total', 'average', 'rank', 'passed', 'teacher_comment', 'principal_comment', 'content_hash', 'published_at', 'generated_at')
    readonly_fields = ('content_hash', 'published_at', 'generated_at')

class ReportWorkflowEventInline(admin.TabularInline):
    model = ReportWorkflowEvent
    extra = 0
    fields = ('report_version', 'actor', 'from_status', 'to_status', 'comment', 'occurred_at')
    readonly_fields = ('occurred_at',)
    autocomplete_fields = ('report_version', 'actor')

class ReportCardLineInline(admin.TabularInline):
    model = ReportCardLine
    extra = 0
    fields = ('subject', 'subject_code', 'subject_name', 'numeric_mark', 'grade_code', 'distinction', 'display_order')
    autocomplete_fields = ('subject',)

class ReportApprovalInline(admin.TabularInline):
    model = ReportApproval
    extra = 0
    fields = ('approver', 'decision', 'comment', 'decided_at')
    readonly_fields = ('decided_at',)
    autocomplete_fields = ('approver',)

@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = ('student_id_display', 'report_period', 'status', 'current_version', 'updated_at')
    list_filter = ('status', 'report_period__academic_year', 'report_period', 'enrollment__class_section__grade_level')
    search_fields = ('enrollment__student__student_id', 'enrollment__student__first_name', 'enrollment__student__last_name', 'report_period__name')
    ordering = ('-updated_at', 'enrollment')
    autocomplete_fields = ('enrollment', 'report_period', 'current_version')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (ReportCardVersionInline, ReportWorkflowEventInline)
    @admin.display(description='Student', ordering='enrollment__student__student_id')
    def student_id_display(self, obj): return obj.enrollment.student.student_id

@admin.register(ReportCardVersion)
class ReportCardVersionAdmin(admin.ModelAdmin):
    list_display = ('report_card', 'version_no', 'average', 'rank', 'passed', 'published_at', 'generated_at')
    list_filter = ('report_card__status', 'report_card__report_period__academic_year', 'passed', 'published_at')
    search_fields = ('report_card__enrollment__student__student_id', 'report_card__enrollment__student__last_name', 'content_hash')
    ordering = ('report_card', '-version_no')
    autocomplete_fields = ('report_card', 'generated_by')
    readonly_fields = ('id', 'content_hash', 'generated_at', 'created_at', 'updated_at')
    inlines = (ReportCardLineInline, ReportApprovalInline)

@admin.register(ReportCardLine)
class ReportCardLineAdmin(admin.ModelAdmin):
    list_display = ('report_version', 'subject_name', 'numeric_mark', 'grade_code', 'distinction', 'display_order')
    list_filter = ('grade_code', 'report_version__report_card__report_period__academic_year')
    search_fields = ('report_version__report_card__enrollment__student__student_id', 'subject_name', 'subject_code', 'grade_code')
    ordering = ('report_version', 'display_order', 'subject_name')
    autocomplete_fields = ('report_version', 'subject')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(ReportApproval)
class ReportApprovalAdmin(admin.ModelAdmin):
    list_display = ('report_version', 'approver', 'decision', 'decided_at')
    list_filter = ('decision', 'decided_at')
    search_fields = ('report_version__report_card__enrollment__student__student_id', 'approver__username', 'approver__last_name')
    ordering = ('-decided_at',)
    autocomplete_fields = ('report_version', 'approver')
    readonly_fields = ('id', 'decided_at', 'created_at', 'updated_at')

@admin.register(ReportWorkflowEvent)
class ReportWorkflowEventAdmin(admin.ModelAdmin):
    list_display = ('report_card', 'from_status', 'to_status', 'actor', 'occurred_at')
    list_filter = ('from_status', 'to_status', 'occurred_at')
    search_fields = ('report_card__enrollment__student__student_id', 'actor__username', 'comment')
    ordering = ('-occurred_at',)
    autocomplete_fields = ('report_card', 'report_version', 'actor')
    readonly_fields = ('id', 'occurred_at', 'created_at', 'updated_at')
