from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from .models import AuditLog
from .permissions import CanViewAuditLogs
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related('actor', 'school')
    serializer_class = AuditLogSerializer
    permission_classes = (CanViewAuditLogs,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ('action', 'entity_type', 'actor', 'school')
    search_fields = ('action', 'entity_type', 'request_id', 'actor__username', 'actor__email', 'school__name')
    ordering_fields = ('created_at', 'action', 'entity_type')
    ordering = ('-created_at',)
