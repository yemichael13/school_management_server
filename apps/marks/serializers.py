from rest_framework import serializers

from apps.reports.models import ReportApproval, ReportCard, ReportCardLine, ReportCardVersion

from .models import Mark, MarkRevision


class MarkSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='enrollment.student.student_id', read_only=True)
    subject_name = serializers.CharField(source='section_subject.subject.name', read_only=True)

    class Meta:
        model = Mark
        fields = ('id', 'enrollment', 'student_id', 'section_subject', 'subject_name', 'value', 'entered_by', 'status', 'locked_by', 'locked_at', 'finalized_by', 'finalized_at', 'created_at', 'updated_at')
        read_only_fields = ('id', 'student_id', 'subject_name', 'entered_by', 'status', 'locked_by', 'locked_at', 'finalized_by', 'finalized_at', 'created_at', 'updated_at')


class MarkRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarkRevision
        fields = ('id', 'mark', 'version_no', 'value', 'changed_by', 'reason', 'created_at', 'updated_at')
        read_only_fields = fields


class ReportCardLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCardLine
        fields = ('id', 'subject', 'subject_code', 'subject_name', 'numeric_mark', 'grade_code', 'distinction', 'display_order')


class ReportCardVersionSerializer(serializers.ModelSerializer):
    lines = ReportCardLineSerializer(many=True, read_only=True)

    class Meta:
        model = ReportCardVersion
        fields = ('id', 'version_no', 'total', 'average', 'rank', 'distinction', 'passed', 'teacher_comment', 'principal_comment', 'published_at', 'generated_by', 'generated_at', 'lines')


class ReportCardSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='enrollment.student.student_id', read_only=True)
    current_version = ReportCardVersionSerializer(read_only=True)

    class Meta:
        model = ReportCard
        fields = ('id', 'enrollment', 'student_id', 'report_period', 'status', 'current_version', 'created_at', 'updated_at')
        read_only_fields = ('id', 'student_id', 'status', 'current_version', 'created_at', 'updated_at')


class ReportReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=ReportApproval.Decision.choices)
    comment = serializers.CharField(required=False, allow_blank=True)

