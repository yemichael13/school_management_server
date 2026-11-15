from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'entity_type', 'entity_id', 'actor', 'school', 'request_id')
    list_filter = ('action', 'entity_type', 'school', 'created_at')
    search_fields = ('action', 'entity_type', 'request_id', 'actor__username', 'entity_id')
    ordering = ('-created_at',)
    autocomplete_fields = ('actor', 'school')
    readonly_fields = ('id', 'actor', 'school', 'action', 'entity_type', 'entity_id', 'before', 'after', 'request_id', 'ip_address', 'created_at', 'updated_at')
    list_per_page = 100
