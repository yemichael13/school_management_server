from django.db import transaction

from .models import Notification


class NotificationService:
    @staticmethod
    @transaction.atomic
    def report_published(*, report_card):
        user = report_card.enrollment.student.user
        user_id = getattr(user, 'id', None)
        if not user_id:
            return []
        version = report_card.current_version
        payload = {'report_card_id': str(report_card.id), 'report_version_id': str(version.id)}
        notifications = []
        items = (
            (Notification.Type.RESULTS_PUBLISHED, 'Results Published', f'Your results for {report_card.report_period.name} are now published.', 'results-published'),
            (Notification.Type.REPORT_READY, 'Report Ready', f'Your {report_card.report_period.name} report is ready to view.', 'report-ready'),
        )
        for notification_type, title, message, key_prefix in items:
            notification, _ = Notification.objects.get_or_create(
                dedupe_key=f'{key_prefix}:{version.id}',
                defaults={'recipient_id': user_id, 'notification_type': notification_type, 'title': title, 'message': message, 'payload': payload},
            )
            notifications.append(notification)
        return notifications
