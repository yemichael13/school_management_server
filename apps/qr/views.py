from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import QRVerificationSerializer
from .services import QRVerificationService


class PublicQRVerificationView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        serializer = QRVerificationSerializer(data={'token': request.query_params.get('token', '')})
        serializer.is_valid(raise_exception=True)
        result = QRVerificationService.verify(raw_token=serializer.validated_data['token'], request=request)
        return Response(result, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = QRVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = QRVerificationService.verify(raw_token=serializer.validated_data['token'], request=request)
        return Response(result, status=status.HTTP_200_OK)
