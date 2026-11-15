from django.contrib import admin
from .models import QRToken, QRVerificationEvent

class QRVerificationEventInline(admin.TabularInline):
    model = QRVerificationEvent
    extra = 0
    fields = ('result', 'ip_address', 'user_agent_hash', 'verified_at')
    readonly_fields = ('verified_at',)

@admin.register(QRToken)
class QRTokenAdmin(admin.ModelAdmin):
    list_display = ('report_version', 'token_version', 'is_active', 'expires_at', 'revoked_at', 'created_at')
    list_filter = ('is_active', 'token_version', 'expires_at', 'revoked_at')
    search_fields = ('report_version__report_card__enrollment__student__student_id', 'token_hash')
    ordering = ('-created_at',)
    autocomplete_fields = ('report_version',)
    readonly_fields = ('id', 'token_hash', 'created_at', 'updated_at')
    inlines = (QRVerificationEventInline,)

@admin.register(QRVerificationEvent)
class QRVerificationEventAdmin(admin.ModelAdmin):
    list_display = ('qr_token', 'result', 'ip_address', 'verified_at')
    list_filter = ('result', 'verified_at')
    search_fields = ('qr_token__token_hash', 'qr_token__report_version__report_card__enrollment__student__student_id')
    ordering = ('-verified_at',)
    autocomplete_fields = ('qr_token',)
    readonly_fields = ('id', 'attempted_token_hash', 'verified_at', 'created_at', 'updated_at')
