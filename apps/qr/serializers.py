from rest_framework import serializers


class QRVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, trim_whitespace=True, max_length=512)
