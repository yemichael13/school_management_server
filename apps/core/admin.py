from django.contrib import admin
from .models import School, SchoolLevel, SchoolMembership, PrincipalScope, SchoolSetting

class SchoolMembershipInline(admin.TabularInline):
    model = SchoolMembership
    extra = 0
    autocomplete_fields = ('user',)
    fields = ('user', 'role', 'is_active', 'starts_on', 'ends_on')

class SchoolSettingInline(admin.TabularInline):
    model = SchoolSetting
    extra = 0
    readonly_fields = ('id', 'created_at', 'updated_at')
    fields = ('setting_key', 'version_no', 'is_current', 'value', 'created_at', 'updated_at')

class GradeLevelInline(admin.TabularInline):
    from apps.academics.models import GradeLevel
    model = GradeLevel
    extra = 0
    fields = ('code', 'name', 'display_order', 'is_active')

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'phone', 'email')
    list_filter = ('is_active',)
    search_fields = ('code', 'name', 'email', 'phone')
    ordering = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (SchoolMembershipInline, SchoolSettingInline)
    list_per_page = 30

@admin.register(SchoolLevel)
class SchoolLevelAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'display_order')
    list_filter = ('code',)
    search_fields = ('code', 'name')
    ordering = ('display_order', 'name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (GradeLevelInline,)

@admin.register(SchoolMembership)
class SchoolMembershipAdmin(admin.ModelAdmin):
    list_display = ('school', 'user', 'role', 'is_active', 'starts_on', 'ends_on')
    list_filter = ('school', 'role', 'is_active')
    search_fields = ('school__name', 'school__code', 'user__username', 'user__email')
    ordering = ('school', 'role', 'user')
    autocomplete_fields = ('school', 'user')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(PrincipalScope)
class PrincipalScopeAdmin(admin.ModelAdmin):
    list_display = ('membership', 'school_level')
    list_filter = ('school_level',)
    search_fields = ('membership__school__name', 'membership__user__username')
    ordering = ('membership', 'school_level')
    autocomplete_fields = ('membership', 'school_level')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(SchoolSetting)
class SchoolSettingAdmin(admin.ModelAdmin):
    list_display = ('school', 'setting_key', 'version_no', 'is_current', 'updated_at')
    list_filter = ('school', 'is_current', 'setting_key')
    search_fields = ('school__name', 'school__code', 'setting_key')
    ordering = ('school', 'setting_key', '-version_no')
    autocomplete_fields = ('school',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 50
