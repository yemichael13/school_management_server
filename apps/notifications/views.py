from django.db.models import Q
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .permissions import NotificationPermission
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = (NotificationPermission,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('created_at', 'read_at')
    ordering = ('-created_at',)

    def get_queryset(self):
        now = timezone.now()
        return Notification.objects.filter(recipient=self.request.user).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))

    @action(detail=True, methods=('post',))
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_read()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=('get',), url_path='unread-count')
    def unread_count(self, request):
        return Response({'unread_count': self.get_queryset().filter(read_at__isnull=True).count()})

    @action(detail=False, methods=('post',), url_path='mark-all-read')
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(read_at__isnull=True).update(read_at=timezone.now(), updated_at=timezone.now())
        return Response({'marked_read': updated}, status=status.HTTP_200_OK)
