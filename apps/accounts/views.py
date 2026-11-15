from django.contrib.auth import update_session_auth_hash
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.audit.services import AuditService
from .serializers import (ChangePasswordSerializer, EmailVerificationRequestSerializer, EmailVerificationSerializer, ForgotPasswordSerializer, LoginSerializer, LogoutSerializer, PasswordResetConfirmSerializer, UserSummarySerializer)

class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

class RefreshTokenView(TokenRefreshView):
    permission_classes = (AllowAny,)

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data['refresh']).blacklist()
        except TokenError:
            return Response({'detail': 'Refresh token is invalid or already revoked.'}, status=status.HTTP_400_BAD_REQUEST)
        AuditService.record(action='logout', entity_type='user', entity_id=request.user.id, actor=request.user, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ForgotPasswordView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'If an account exists for that email, a password reset link has been sent.'})

class PasswordResetConfirmView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password has been reset successfully.'})

class RequestEmailVerificationView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        serializer = EmailVerificationRequestSerializer(data={}, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if not user.email:
            return Response({'detail': 'Add an email address before requesting verification.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'If the account has an unverified email, a verification link has been sent.'})

class VerifyEmailView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Email verified successfully.'})

class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        update_session_auth_hash(request, user)
        AuditService.record(action='password_changed', entity_type='user', entity_id=user.id, actor=user, request=request)
        return Response({'detail': 'Password changed successfully.'})

class MeView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        return Response(UserSummarySerializer(request.user).data)
