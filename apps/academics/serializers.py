from rest_framework import serializers

from apps.core.models import SchoolLevel
from .models import AcademicYear, ClassSection, GradeLevel, SectionSubject, Semester, Subject
from .services import gregorian_to_ethiopian, semester_is_within_academic_year


class EthiopianDateMixin:
    def _ethiopian_date(self, value):
        return gregorian_to_ethiopian(value) if value else None


class SchoolLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolLevel
        fields = ('id', 'code', 'name', 'display_order')
        read_only_fields = ('id',)


class AcademicYearSerializer(EthiopianDateMixin, serializers.ModelSerializer):
    start_date_ethiopian = serializers.SerializerMethodField()
    end_date_ethiopian = serializers.SerializerMethodField()
    school_name = serializers.CharField(source='school.name', read_only=True)

    class Meta:
        model = AcademicYear
        fields = ('id', 'school', 'school_name', 'code', 'start_date', 'end_date', 'start_date_ethiopian', 'end_date_ethiopian', 'status', 'is_current', 'created_at', 'updated_at')
        read_only_fields = ('id', 'school_name', 'start_date_ethiopian', 'end_date_ethiopian', 'created_at', 'updated_at')

    def get_start_date_ethiopian(self, obj): return self._ethiopian_date(obj.start_date)
    def get_end_date_ethiopian(self, obj): return self._ethiopian_date(obj.end_date)

    def validate(self, attrs):
        start = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        if start and end and end <= start:
            raise serializers.ValidationError({'end_date': 'End date must be after the start date.'})
        return attrs


class SemesterSerializer(EthiopianDateMixin, serializers.ModelSerializer):
    starts_on_ethiopian = serializers.SerializerMethodField()
    ends_on_ethiopian = serializers.SerializerMethodField()
    academic_year_code = serializers.CharField(source='academic_year.code', read_only=True)

    class Meta:
        model = Semester
        fields = ('id', 'academic_year', 'academic_year_code', 'code', 'name', 'sequence', 'starts_on', 'ends_on', 'starts_on_ethiopian', 'ends_on_ethiopian', 'status', 'is_current', 'created_at', 'updated_at')
        read_only_fields = ('id', 'academic_year_code', 'starts_on_ethiopian', 'ends_on_ethiopian', 'created_at', 'updated_at')

    def get_starts_on_ethiopian(self, obj): return self._ethiopian_date(obj.starts_on)
    def get_ends_on_ethiopian(self, obj): return self._ethiopian_date(obj.ends_on)

    def validate(self, attrs):
        start = attrs.get('starts_on', getattr(self.instance, 'starts_on', None))
        end = attrs.get('ends_on', getattr(self.instance, 'ends_on', None))
        if start and end and end < start:
            raise serializers.ValidationError({'ends_on': 'End date must be on or after the start date.'})
        academic_year = attrs.get('academic_year', getattr(self.instance, 'academic_year', None))
        if academic_year and start and end and not semester_is_within_academic_year(academic_year, start, end):
            raise serializers.ValidationError({'starts_on': 'Semester dates must fall within the academic year.'})
        return attrs


class GradeLevelSerializer(serializers.ModelSerializer):
    school_level_name = serializers.CharField(source='school_level.name', read_only=True)

    class Meta:
        model = GradeLevel
        fields = ('id', 'school_level', 'school_level_name', 'code', 'name', 'display_order', 'is_active')
        read_only_fields = ('id', 'school_level_name')


class ClassSectionSerializer(serializers.ModelSerializer):
    academic_year_code = serializers.CharField(source='academic_year.code', read_only=True)
    grade_level_name = serializers.CharField(source='grade_level.name', read_only=True)

    class Meta:
        model = ClassSection
        fields = ('id', 'academic_year', 'academic_year_code', 'grade_level', 'grade_level_name', 'code', 'name', 'capacity', 'is_active')
        read_only_fields = ('id', 'academic_year_code', 'grade_level_name')


class SubjectSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)

    class Meta:
        model = Subject
        fields = ('id', 'school', 'school_name', 'code', 'name', 'description', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'school_name', 'created_at', 'updated_at')


class SectionSubjectSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source='class_section.name', read_only=True)
    section_code = serializers.CharField(source='class_section.code', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)

    class Meta:
        model = SectionSubject
        fields = ('id', 'class_section', 'section_name', 'section_code', 'subject', 'subject_name', 'subject_code', 'grading_scheme', 'display_order', 'is_required', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'section_name', 'section_code', 'subject_name', 'subject_code', 'created_at', 'updated_at')
