from django.contrib import admin
from .models import Promotion, PromotionApproval

class PromotionApprovalInline(admin.TabularInline):
    model = PromotionApproval
    extra = 0
    fields = ('role', 'approver', 'decision', 'comment', 'decided_at')
    readonly_fields = ('decided_at',)
    autocomplete_fields = ('approver',)

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('student_id_display', 'source_enrollment', 'target_grade_level', 'target_academic_year', 'status', 'effective_on', 'proposed_at', 'completed_at')
    list_filter = ('status', 'target_academic_year', 'target_grade_level__school_level', 'proposed_at')
    search_fields = ('source_enrollment__student__student_id', 'source_enrollment__student__first_name', 'source_enrollment__student__last_name', 'target_grade_level__name')
    ordering = ('-proposed_at',)
    autocomplete_fields = ('source_enrollment', 'target_academic_year', 'target_grade_level', 'target_class_section', 'target_enrollment', 'proposed_by')
    readonly_fields = ('id', 'proposed_at', 'completed_at', 'created_at', 'updated_at')
    inlines = (PromotionApprovalInline,)
    @admin.display(description='Student', ordering='source_enrollment__student__student_id')
    def student_id_display(self, obj): return obj.source_enrollment.student.student_id

@admin.register(PromotionApproval)
class PromotionApprovalAdmin(admin.ModelAdmin):
    list_display = ('promotion', 'role', 'approver', 'decision', 'decided_at')
    list_filter = ('role', 'decision', 'decided_at')
    search_fields = ('promotion__source_enrollment__student__student_id', 'approver__username')
    ordering = ('promotion', 'role', '-decided_at')
    autocomplete_fields = ('promotion', 'approver')
    readonly_fields = ('id', 'decided_at', 'created_at', 'updated_at')
