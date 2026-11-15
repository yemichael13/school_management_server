from rest_framework import serializers


class AnalyticsFilterSerializer(serializers.Serializer):
    school = serializers.UUIDField(required=False)
    academic_year = serializers.UUIDField(required=False)
    report_period = serializers.UUIDField(required=False)
    class_section = serializers.UUIDField(required=False)
    subject = serializers.UUIDField(required=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=10)
