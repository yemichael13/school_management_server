from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)

    class Meta:
        model = AuditLog
        fields = ('id', 'created_at', 'action', 'entity_type', 'entity_id', 'actor', 'actor_username', 'school', 'school_name', 'before', 'after', 'request_id', 'ip_address')
        read_only_fields = fields
