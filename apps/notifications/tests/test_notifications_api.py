from types import SimpleNamespace
from uuid import uuid4

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User

from apps.notifications.models import Notification
from apps.notifications.services import NotificationService


class NotificationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='student', password='StrongPass123!', role=User.Role.STUDENT)
        self.other = User.objects.create_user(username='other', password='StrongPass123!', role=User.Role.STUDENT)
        Notification.objects.create(recipient=self.user, notification_type=Notification.Type.RESULTS_PUBLISHED, title='Results Published', message='Results are ready.', payload={'report_id': '1'})
        Notification.objects.create(recipient=self.user, notification_type=Notification.Type.REPORT_READY, title='Report Ready', message='Report is ready.', payload={'report_id': '1'})
        Notification.objects.create(recipient=self.other, notification_type=Notification.Type.SYSTEM, title='Other', message='Other user notification.')

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def test_list_and_unread_count_are_scoped_to_recipient(self):
        self.authenticate()
        response = self.client.get('/api/notifications/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        count = self.client.get('/api/notifications/notifications/unread-count/')
        self.assertEqual(count.data['unread_count'], 2)

    def test_student_can_mark_one_notification_as_read(self):
        self.authenticate()
        notification = Notification.objects.filter(recipient=self.user).first()
        response = self.client.post(f'/api/notifications/notifications/{notification.id}/read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])
        self.assertEqual(self.client.get('/api/notifications/notifications/unread-count/').data['unread_count'], 1)

    def test_mark_all_read_and_other_recipient_are_protected(self):
        self.authenticate()
        response = self.client.post('/api/notifications/notifications/mark-all-read/')
        self.assertEqual(response.data['marked_read'], 2)
        self.assertEqual(self.client.get('/api/notifications/notifications/unread-count/').data['unread_count'], 0)
        other_notification = Notification.objects.filter(recipient=self.other).first()
        self.assertEqual(self.client.get(f'/api/notifications/notifications/{other_notification.id}/').status_code, status.HTTP_404_NOT_FOUND)

    def test_report_notifications_are_idempotent(self):
        period = SimpleNamespace(name='Semester 1')
        version = SimpleNamespace(id=uuid4())
        report_card = SimpleNamespace(id=uuid4(), current_version=version, report_period=period, enrollment=SimpleNamespace(student=SimpleNamespace(user=self.user)))
        first = NotificationService.report_published(report_card=report_card)
        second = NotificationService.report_published(report_card=report_card)
        self.assertEqual(len(first), 2)
        self.assertEqual(len(second), 2)
        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), 4)
