from django.urls import path
from .views import (ChangePasswordView, ForgotPasswordView, LoginView, LogoutView, MeView, PasswordResetConfirmView, RefreshTokenView, RequestEmailVerificationView, VerifyEmailView)

app_name = 'accounts'
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password/forgot/', ForgotPasswordView.as_view(), name='password_forgot'),
    path('password/reset/', PasswordResetConfirmView.as_view(), name='password_reset'),
    path('password/change/', ChangePasswordView.as_view(), name='password_change'),
    path('email/request-verification/', RequestEmailVerificationView.as_view(), name='email_request_verification'),
    path('email/verify/', VerifyEmailView.as_view(), name='email_verify'),
    path('me/', MeView.as_view(), name='me'),
]
