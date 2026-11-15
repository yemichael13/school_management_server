from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User

from apps.audit.models import AuditLog
from apps.audit.services import AuditService


class AuditLogTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password='StrongPass123!', role=User.Role.ADMIN)
        self.teacher = User.objects.create_user(username='teacher', password='StrongPass123!', role=User.Role.TEACHER)

    def test_successful_and_failed_logins_are_audited(self):
        success = self.client.post('/api/auth/login/', {'username': 'admin', 'password': 'StrongPass123!'}, format='json')
        self.assertEqual(success.status_code, status.HTTP_200_OK)
        failed = self.client.post('/api/auth/login/', {'username': 'admin', 'password': 'wrong-password'}, format='json')
        self.assertEqual(failed.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(AuditLog.objects.filter(action='login_success').count(), 1)
        self.assertEqual(AuditLog.objects.filter(action='login_failed').count(), 1)

    def test_audit_api_is_searchable_and_manager_only(self):
        AuditService.record(action='mark_edited', entity_type='mark', actor=self.admin, after={'value': Decimal('88.50')})
        AuditService.record(action='qr_verification', entity_type='qr_token', after={'result': 'invalid'})
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/audit/logs/?search=mark_edited')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['after']['value'], '88.50')
        self.client.force_authenticate(user=self.teacher)
        self.assertEqual(self.client.get('/api/audit/logs/').status_code, status.HTTP_403_FORBIDDEN)

    def test_requested_event_types_are_supported(self):
        for action in ('mark_unlocked', 'report_published', 'user_action', 'qr_verification'):
            AuditService.record(action=action, entity_type='test', actor=self.admin)
        self.assertEqual(AuditLog.objects.filter(action__in=('mark_unlocked', 'report_published', 'user_action', 'qr_verification')).count(), 4)
