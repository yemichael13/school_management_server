from rest_framework import serializers

from apps.reports.models import ReportCardLine


class PortalReportLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCardLine
        fields = ('subject_code', 'subject_name', 'numeric_mark', 'grade_code', 'distinction', 'display_order')


class PortalReportSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='pk')
    report_period = serializers.CharField(source='report_period.name')
    status = serializers.CharField()
    version = serializers.IntegerField(source='current_version.version_no')
    total = serializers.DecimalField(source='current_version.total', max_digits=8, decimal_places=2, allow_null=True)
    average = serializers.DecimalField(source='current_version.average', max_digits=6, decimal_places=2, allow_null=True)
    rank = serializers.IntegerField(source='current_version.rank', allow_null=True)
    distinction = serializers.CharField(source='current_version.distinction')
    teacher_comment = serializers.CharField(source='current_version.teacher_comment')
    principal_comment = serializers.CharField(source='current_version.principal_comment')
    lines = serializers.SerializerMethodField()

    def get_lines(self, obj):
        return PortalReportLineSerializer(obj.current_version.lines.all(), many=True).data


class PortalTimetableSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    weekday = serializers.CharField(source='get_weekday_display')
    starts_at = serializers.TimeField()
    ends_at = serializers.TimeField()
    room = serializers.CharField()
    subject = serializers.CharField(source='section_subject.subject.name')
    subject_code = serializers.CharField(source='section_subject.subject.code')
    teachers = serializers.SerializerMethodField()

    def get_teachers(self, obj):
        return [assignment.teacher.user.get_full_name() or assignment.teacher.user.username for assignment in obj.section_subject.teaching_assignments.all() if assignment.is_active]
