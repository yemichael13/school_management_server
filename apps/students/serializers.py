from rest_framework import serializers

from apps.academics.models import AcademicYear, ClassSection, GradeLevel
from .models import StudentEnrollment, StudentProfile


class StudentProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    current_enrollment = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = (
            'id', 'school', 'user', 'student_id', 'first_name', 'middle_name',
            'last_name', 'full_name', 'birth_date', 'sex', 'admitted_on',
            'photo', 'is_active', 'current_enrollment', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'full_name', 'current_enrollment', 'created_at', 'updated_at')

    def get_current_enrollment(self, obj):
        enrollment = obj.enrollments.filter(status=StudentEnrollment.Status.ACTIVE).select_related('academic_year', 'class_section', 'class_section__grade_level').first()
        return EnrollmentSummarySerializer(enrollment).data if enrollment else None


class EnrollmentSummarySerializer(serializers.ModelSerializer):
    academic_year_code = serializers.CharField(source='academic_year.code', read_only=True)
    section_name = serializers.CharField(source='class_section.name', read_only=True)
    grade_level_name = serializers.CharField(source='class_section.grade_level.name', read_only=True)

    class Meta:
        model = StudentEnrollment
        fields = ('id', 'enrollment_number', 'academic_year', 'academic_year_code', 'class_section', 'section_name', 'grade_level_name', 'started_on', 'ended_on', 'status', 'exit_reason')


class StudentHistorySerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(read_only=True)
    academic_year_code = serializers.CharField(source='academic_year.code', read_only=True)
    section_name = serializers.CharField(source='class_section.name', read_only=True)
    grade_level_name = serializers.CharField(source='class_section.grade_level.name', read_only=True)

    class Meta:
        model = StudentEnrollment
        fields = ('id', 'student', 'enrollment_number', 'academic_year', 'academic_year_code', 'class_section', 'section_name', 'grade_level_name', 'started_on', 'ended_on', 'status', 'exit_reason')


class EnrollmentActionSerializer(serializers.Serializer):
    academic_year = serializers.PrimaryKeyRelatedField(queryset=AcademicYear.objects.all())
    class_section = serializers.PrimaryKeyRelatedField(queryset=ClassSection.objects.all())
    effective_on = serializers.DateField()
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)


class PromotionRequestSerializer(EnrollmentActionSerializer):
    target_grade_level = serializers.PrimaryKeyRelatedField(queryset=GradeLevel.objects.all())


class LifecycleActionSerializer(serializers.Serializer):
    effective_on = serializers.DateField()
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)


class ExcelImportSerializer(serializers.Serializer):
    school = serializers.UUIDField()
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.lower().endswith(('.xlsx', '.xlsm')):
            raise serializers.ValidationError('Upload an .xlsx or .xlsm workbook.')
        return value
