from rest_framework.permissions import IsAuthenticated


class NotificationPermission(IsAuthenticated):
    pass
