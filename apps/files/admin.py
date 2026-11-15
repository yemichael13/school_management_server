from django.contrib import admin
from .models import ReportDocument

@admin.register(ReportDocument)
class ReportDocumentAdmin(admin.ModelAdmin):
    list_display = ('report_version', 'backend', 'object_key', 'checksum', 'generated_by', 'generated_at')
    list_filter = ('backend', 'generated_at')
    search_fields = ('object_key', 'checksum', 'report_version__report_card__enrollment__student__student_id')
    ordering = ('report_version', '-generated_at')
    autocomplete_fields = ('report_version', 'generated_by')
    readonly_fields = ('id', 'checksum', 'generated_at', 'created_at', 'updated_at')
