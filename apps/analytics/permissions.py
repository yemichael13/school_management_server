from rest_framework.permissions import BasePermission


ANALYTICS_ROLES = frozenset({'admin', 'principal', 'kindergarten_principal', 'primary_principal', 'teacher'})


class CanViewAnalytics(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.role in ANALYTICS_ROLES))
