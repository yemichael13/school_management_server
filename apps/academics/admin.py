from django.contrib import admin
from .models import AcademicYear, Semester, GradeLevel, ClassSection, Subject, GradingScheme, GradingRule, SectionSubject, ReportPeriod, TimetableEntry

class ClassSectionInline(admin.TabularInline):
    model = ClassSection
    extra = 0
    fields = ('grade_level', 'code', 'name', 'capacity', 'is_active')
    autocomplete_fields = ('grade_level',)

class ReportPeriodInline(admin.TabularInline):
    model = ReportPeriod
    extra = 0
    fields = ('code', 'name', 'sequence', 'starts_on', 'ends_on', 'is_published')

class SemesterInline(admin.TabularInline):
    model = Semester
    extra = 0
    fields = ('code', 'name', 'sequence', 'starts_on', 'ends_on', 'status', 'is_current')

class GradingSchemeInline(admin.TabularInline):
    model = GradingScheme
    extra = 0
    fields = ('school_level', 'name', 'passing_mark', 'is_active')
    autocomplete_fields = ('school_level',)

class GradingRuleInline(admin.TabularInline):
    model = GradingRule
    extra = 0
    fields = ('min_mark', 'max_mark', 'grade_code', 'distinction', 'display_order')
    readonly_fields = ('mark_range',)

class SectionSubjectInline(admin.TabularInline):
    model = SectionSubject
    extra = 0
    fields = ('subject', 'grading_scheme', 'display_order', 'is_required', 'is_active')
    autocomplete_fields = ('subject', 'grading_scheme')

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('school', 'code', 'start_date', 'end_date', 'status', 'is_current')
    list_filter = ('school', 'status', 'is_current')
    search_fields = ('school__name', 'school__code', 'code')
    ordering = ('-start_date', 'code')
    autocomplete_fields = ('school',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (ClassSectionInline, SemesterInline, ReportPeriodInline, GradingSchemeInline)
    list_per_page = 30

@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ('school_level', 'code', 'name', 'display_order', 'is_active')
    list_filter = ('school_level', 'is_active')
    search_fields = ('code', 'name', 'school_level__name')
    ordering = ('school_level', 'display_order')
    autocomplete_fields = ('school_level',)
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'sequence', 'code', 'name', 'starts_on', 'ends_on', 'status', 'is_current')
    list_filter = ('academic_year', 'status', 'is_current')
    search_fields = ('academic_year__code', 'code', 'name')
    ordering = ('academic_year', 'sequence')
    autocomplete_fields = ('academic_year',)
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(ClassSection)
class ClassSectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'grade_level', 'academic_year', 'capacity', 'is_active')
    list_filter = ('academic_year', 'grade_level__school_level', 'grade_level', 'is_active')
    search_fields = ('name', 'code', 'academic_year__code', 'grade_level__name')
    ordering = ('academic_year', 'grade_level__display_order', 'code')
    autocomplete_fields = ('academic_year', 'grade_level')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (SectionSubjectInline,)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('school', 'code', 'name', 'is_active')
    list_filter = ('school', 'is_active')
    search_fields = ('school__name', 'school__code', 'code', 'name', 'description')
    ordering = ('name',)
    autocomplete_fields = ('school',)
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(GradingScheme)
class GradingSchemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'academic_year', 'school_level', 'passing_mark', 'is_active')
    list_filter = ('school', 'academic_year', 'school_level', 'is_active', 'calculates_rank', 'calculates_pass_fail')
    search_fields = ('name', 'school__name', 'academic_year__code', 'school_level__name')
    ordering = ('school', 'academic_year', 'school_level', 'name')
    autocomplete_fields = ('school', 'academic_year', 'school_level')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (GradingRuleInline,)

@admin.register(GradingRule)
class GradingRuleAdmin(admin.ModelAdmin):
    list_display = ('grading_scheme', 'min_mark', 'max_mark', 'grade_code', 'distinction', 'display_order')
    list_filter = ('grading_scheme__school_level', 'grading_scheme', 'grade_code')
    search_fields = ('grading_scheme__name', 'grade_code', 'distinction')
    ordering = ('grading_scheme', '-min_mark')
    autocomplete_fields = ('grading_scheme',)
    readonly_fields = ('id', 'mark_range', 'created_at', 'updated_at')

@admin.register(SectionSubject)
class SectionSubjectAdmin(admin.ModelAdmin):
    list_display = ('class_section', 'subject', 'grading_scheme', 'display_order', 'is_required', 'is_active')
    list_filter = ('class_section__academic_year', 'class_section__grade_level', 'subject', 'is_required', 'is_active')
    search_fields = ('class_section__name', 'class_section__code', 'subject__name', 'subject__code')
    ordering = ('class_section', 'display_order', 'subject__name')
    autocomplete_fields = ('class_section', 'subject', 'grading_scheme')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ('class_section', 'weekday', 'starts_at', 'ends_at', 'section_subject', 'room', 'is_active')
    list_filter = ('class_section__academic_year', 'class_section__grade_level', 'weekday', 'is_active')
    search_fields = ('class_section__name', 'section_subject__subject__name', 'room')
    ordering = ('class_section', 'weekday', 'starts_at')
    autocomplete_fields = ('class_section', 'section_subject')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(ReportPeriod)
class ReportPeriodAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'code', 'name', 'sequence', 'starts_on', 'ends_on', 'is_published')
    list_filter = ('academic_year', 'is_published')
    search_fields = ('academic_year__code', 'code', 'name')
    ordering = ('academic_year', 'sequence')
    autocomplete_fields = ('academic_year',)
    readonly_fields = ('id', 'created_at', 'updated_at')
