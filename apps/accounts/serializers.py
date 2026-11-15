from base64 import urlsafe_b64decode, urlsafe_b64encode
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.audit.services import AuditService

User = get_user_model()

class UserSummarySerializer(serializers.ModelSerializer):
    role_label = serializers.CharField(source='get_role_display', read_only=True)
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'role_label', 'email_verified_at')
        read_only_fields = fields

class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        try:
            data = super().validate(attrs)
        except (serializers.ValidationError, AuthenticationFailed):
            failed_user = User.objects.filter(username=attrs.get('username', '')).first()
            AuditService.record(action='login_failed', entity_type='user', entity_id=failed_user.id if failed_user else None, actor=None, school=failed_user.school_memberships.filter(is_active=True).first().school if failed_user and failed_user.school_memberships.filter(is_active=True).exists() else None, after={'username': attrs.get('username', '')}, request=self.context.get('request'))
            raise
        data['user'] = UserSummarySerializer(self.user).data
        AuditService.record(action='login_success', entity_type='user', entity_id=self.user.id, actor=self.user, after={'username': self.user.username}, request=self.context.get('request'))
        return data

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    def save(self, **kwargs):
        email = self.validated_data['email']
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            url = f"{settings.FRONTEND_PASSWORD_RESET_URL}?uid={uid}&token={token}"
            send_mail('Reset your Degnetu password', f'Use this link to reset your password: {url}', settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        return user

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        try:
            user_id = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({'token': 'This reset link is invalid or expired.'})
        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({'token': 'This reset link is invalid or expired.'})
        password_validation.validate_password(attrs['new_password'], user)
        attrs['user'] = user
        return attrs
    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user

class EmailVerificationRequestSerializer(serializers.Serializer):
    def save(self, **kwargs):
        user = self.context['request'].user
        if user.email and not user.email_verified_at:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            url = f"{settings.FRONTEND_EMAIL_VERIFICATION_URL}?uid={uid}&token={token}"
            send_mail('Verify your Degnetu email', f'Verify your email using this link: {url}', settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        return user

class EmailVerificationSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({'token': 'This verification link is invalid or expired.'})
        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({'token': 'This verification link is invalid or expired.'})
        attrs['user'] = user
        return attrs
    def save(self, **kwargs):
        user = self.validated_data['user']
        if not user.email_verified_at:
            user.email_verified_at = timezone.now()
            user.save(update_fields=['email_verified_at'])
        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({'old_password': 'The current password is incorrect.'})
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        password_validation.validate_password(attrs['new_password'], user)
        return attrs
    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user
