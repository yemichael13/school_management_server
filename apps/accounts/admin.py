from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff', 'last_login', 'email_verified_at')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    readonly_fields = ('id', 'last_login', 'date_joined', 'deleted_at', 'email_verified_at')
    fieldsets = UserAdmin.fieldsets + (('School role and lifecycle', {'fields': ('role', 'deleted_at', 'email_verified_at')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('School role', {'fields': ('role',)}),)
    list_per_page = 50

