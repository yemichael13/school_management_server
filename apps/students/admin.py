from django.contrib import admin
from .models import StudentProfile, Guardian, StudentGuardian, StudentEnrollment, StudentTransfer

class StudentGuardianInline(admin.TabularInline):
    model = StudentGuardian
    extra = 0
    fields = ('guardian', 'relationship', 'is_primary', 'notification_consent')
    autocomplete_fields = ('guardian',)

class StudentEnrollmentInline(admin.TabularInline):
    model = StudentEnrollment
    extra = 0
    fields = ('academic_year', 'class_section', 'enrollment_number', 'started_on', 'ended_on', 'status', 'exit_reason')
    autocomplete_fields = ('academic_year', 'class_section')

class StudentLinkInline(admin.TabularInline):
    model = StudentGuardian
    extra = 0
    fields = ('student', 'relationship', 'is_primary', 'notification_consent')
    autocomplete_fields = ('student',)

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'full_name_display', 'school', 'sex', 'admitted_on', 'is_active', 'user')
    list_filter = ('school', 'sex', 'is_active', 'admitted_on')
    search_fields = ('student_id', 'first_name', 'middle_name', 'last_name', 'user__username', 'user__email')
    ordering = ('last_name', 'first_name', 'student_id')
    autocomplete_fields = ('school', 'user')
    readonly_fields = ('id', 'full_name_display', 'created_at', 'updated_at')
    inlines = (StudentGuardianInline, StudentEnrollmentInline)
    @admin.display(description='Full name', ordering='last_name')
    def full_name_display(self, obj): return obj.full_name

@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ('full_name_display', 'school', 'phone', 'email')
    list_filter = ('school',)
    search_fields = ('first_name', 'last_name', 'phone', 'email', 'school__name')
    ordering = ('last_name', 'first_name')
    autocomplete_fields = ('school',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (StudentLinkInline,)
    @admin.display(description='Name', ordering='last_name')
    def full_name_display(self, obj): return str(obj)

@admin.register(StudentGuardian)
class StudentGuardianAdmin(admin.ModelAdmin):
    list_display = ('student', 'guardian', 'relationship', 'is_primary', 'notification_consent')
    list_filter = ('relationship', 'is_primary', 'notification_consent', 'student__school')
    search_fields = ('student__student_id', 'student__first_name', 'student__last_name', 'guardian__first_name', 'guardian__last_name', 'guardian__phone')
    ordering = ('student', '-is_primary', 'guardian')
    autocomplete_fields = ('student', 'guardian')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('enrollment_number', 'student', 'academic_year', 'class_section', 'status', 'started_on', 'ended_on')
    list_filter = ('academic_year', 'status', 'class_section__grade_level', 'class_section', 'student__school')
    search_fields = ('enrollment_number', 'student__student_id', 'student__first_name', 'student__last_name', 'class_section__name')
    ordering = ('student', '-started_on')
    autocomplete_fields = ('student', 'academic_year', 'class_section')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 50

@admin.register(StudentTransfer)
class StudentTransferAdmin(admin.ModelAdmin):
    list_display = ('source_enrollment', 'destination_enrollment', 'effective_on', 'reason')
    list_filter = ('effective_on',)
    search_fields = ('source_enrollment__student__student_id', 'source_enrollment__student__last_name', 'reason')
    ordering = ('-effective_on',)
    autocomplete_fields = ('source_enrollment', 'destination_enrollment')
    readonly_fields = ('id', 'created_at', 'updated_at')
