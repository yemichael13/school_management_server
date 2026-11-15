from django.urls import path

from .views import PublicQRVerificationView

app_name = 'qr'
urlpatterns = [path('verify/', PublicQRVerificationView.as_view(), name='verify')]
