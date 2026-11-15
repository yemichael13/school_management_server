from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'read_status', 'created_at', 'expires_at')
    list_filter = ('notification_type', 'read_at', 'expires_at', 'created_at')
    search_fields = ('recipient__username', 'recipient__email', 'title', 'message')
    ordering = ('-created_at',)
    autocomplete_fields = ('recipient',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    @admin.display(boolean=True, description='Read')
    def read_status(self, obj): return obj.read_at is not None
