from django.contrib import admin
from .models import ExportJob

@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    list_display = ('export_type', 'school', 'requested_by', 'status', 'created_at', 'completed_at')
    list_filter = ('export_type', 'status', 'school', 'created_at')
    search_fields = ('school__name', 'requested_by__username', 'object_key', 'checksum', 'error_message')
    ordering = ('-created_at',)
    autocomplete_fields = ('requested_by', 'school')
    readonly_fields = ('id', 'requested_by', 'school', 'export_type', 'filters', 'object_key', 'checksum', 'error_message', 'started_at', 'completed_at', 'created_at', 'updated_at')
