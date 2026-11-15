from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.models import School, SchoolLevel, SchoolMembership, PrincipalScope
from apps.accounts.models import User
from apps.accounts.permissions import IsAdmin, IsKindergartenPrincipal, IsPrimaryPrincipal, IsStudent, IsTeacher

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AuthenticationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='teacher1', email='teacher@example.com', password='StrongPass123!', role=User.Role.TEACHER)
        self.admin = User.objects.create_user(username='admin1', email='admin@example.com', password='StrongPass123!', role=User.Role.ADMIN)

    def login(self, username='teacher1', password='StrongPass123!'):
        return self.client.post('/api/auth/login/', {'username': username, 'password': password}, format='json')

    def test_login_returns_access_refresh_and_user(self):
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], User.Role.TEACHER)

    def test_refresh_and_logout_blacklist_refresh_token(self):
        login = self.login()
        refresh = login.data['refresh']
        refreshed = self.client.post('/api/auth/token/refresh/', {'refresh': refresh}, format='json')
        self.assertEqual(refreshed.status_code, status.HTTP_200_OK)
        refresh = refreshed.data.get('refresh', refresh)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        logout = self.client.post('/api/auth/logout/', {'refresh': refresh}, format='json')
        self.assertEqual(logout.status_code, status.HTTP_204_NO_CONTENT)
        revoked_refresh = self.client.post('/api/auth/token/refresh/', {'refresh': refresh}, format='json')
        self.assertEqual(revoked_refresh.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_me_and_change_password(self):
        login = self.login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        me = self.client.get('/api/auth/me/')
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        changed = self.client.post('/api/auth/password/change/', {'old_password': 'StrongPass123!', 'new_password': 'NewStrongPass123!', 'new_password_confirm': 'NewStrongPass123!'}, format='json')
        self.assertEqual(changed.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPass123!'))

    def test_forgot_password_is_non_enumerating_and_sends_email(self):
        response = self.client.post('/api/auth/password/forgot/', {'email': self.user.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        unknown = self.client.post('/api/auth/password/forgot/', {'email': 'unknown@example.com'}, format='json')
        self.assertEqual(unknown.status_code, status.HTTP_200_OK)

    def test_email_verification(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.login().data['access']}")
        requested = self.client.post('/api/auth/email/request-verification/')
        self.assertEqual(requested.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('uid=', mail.outbox[0].body)

    def test_unauthenticated_protected_endpoints_are_rejected(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.post('/api/auth/logout/', {'refresh': 'invalid'}, format='json').status_code, status.HTTP_401_UNAUTHORIZED)

class RolePermissionTests(TestCase):
    def make_request(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client.get('/api/auth/me/').wsgi_request

    def test_basic_role_permissions(self):
        admin = User.objects.create_user(username='a', password='StrongPass123!', role=User.Role.ADMIN)
        teacher = User.objects.create_user(username='t', password='StrongPass123!', role=User.Role.TEACHER)
        student = User.objects.create_user(username='s', password='StrongPass123!', role=User.Role.STUDENT)
        self.assertTrue(IsAdmin().has_permission(self.make_request(admin), None))
        self.assertTrue(IsTeacher().has_permission(self.make_request(teacher), None))
        self.assertTrue(IsStudent().has_permission(self.make_request(student), None))
        self.assertFalse(IsAdmin().has_permission(self.make_request(teacher), None))

    def test_principal_scope_permissions(self):
        school = School.objects.create(code='SCH', name='School')
        kindergarten = SchoolLevel.objects.create(code=SchoolLevel.Code.KINDERGARTEN, name='Kindergarten')
        primary = SchoolLevel.objects.create(code=SchoolLevel.Code.PRIMARY, name='Primary')
        principal = User.objects.create_user(username='p', password='StrongPass123!', role=User.Role.PRINCIPAL)
        membership = SchoolMembership.objects.create(school=school, user=principal, role=SchoolMembership.Role.PRINCIPAL)
        PrincipalScope.objects.create(membership=membership, school_level=kindergarten)
        request = self.make_request(principal)
        self.assertTrue(IsKindergartenPrincipal().has_permission(request, None))
        self.assertFalse(IsPrimaryPrincipal().has_permission(request, None))

