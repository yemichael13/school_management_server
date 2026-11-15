from rest_framework import serializers

from .models import TeacherExperience, TeacherProfile, TeacherQualification, TeacherSalary, TeachingAssignment


class TeacherProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    workload = serializers.SerializerMethodField()

    class Meta:
        model = TeacherProfile
        fields = ('id', 'school', 'user', 'full_name', 'employee_number', 'hired_on', 'is_active', 'workload', 'created_at', 'updated_at')
        read_only_fields = ('id', 'full_name', 'workload', 'created_at', 'updated_at')

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_workload(self, obj):
        from .services import TeacherAssignmentService
        return TeacherAssignmentService.workload(obj)


class TeachingAssignmentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='section_subject.subject.name', read_only=True)
    class_name = serializers.CharField(source='section_subject.class_section.name', read_only=True)
    academic_year = serializers.CharField(source='section_subject.class_section.academic_year.code', read_only=True)

    class Meta:
        model = TeachingAssignment
        fields = ('id', 'teacher', 'teacher_name', 'section_subject', 'subject_name', 'class_name', 'academic_year', 'starts_on', 'ends_on', 'is_lead', 'weekly_periods', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'teacher_name', 'subject_name', 'class_name', 'academic_year', 'created_at', 'updated_at')

    def validate(self, attrs):
        start = attrs.get('starts_on', getattr(self.instance, 'starts_on', None))
        end = attrs.get('ends_on', getattr(self.instance, 'ends_on', None))
        if start and end and end < start:
            raise serializers.ValidationError({'ends_on': 'End date must be on or after start date.'})
        return attrs


class TeacherQualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherQualification
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class TeacherExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherExperience
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate(self, attrs):
        start = attrs.get('starts_on', getattr(self.instance, 'starts_on', None))
        end = attrs.get('ends_on', getattr(self.instance, 'ends_on', None))
        if start and end and end < start:
            raise serializers.ValidationError({'ends_on': 'End date must be on or after start date.'})
        return attrs


class TeacherSalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherSalary
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate(self, attrs):
        start = attrs.get('effective_from', getattr(self.instance, 'effective_from', None))
        end = attrs.get('effective_to', getattr(self.instance, 'effective_to', None))
        if start and end and end < start:
            raise serializers.ValidationError({'effective_to': 'Effective end must be on or after start date.'})
        return attrs

