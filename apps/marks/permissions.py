from rest_framework.permissions import BasePermission


MANAGERS = frozenset({'admin', 'principal', 'kindergarten_principal', 'primary_principal'})


class MarkPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.role in MANAGERS:
            return True
        return user.role == 'teacher' and request.method in ('GET', 'POST', 'PUT', 'PATCH')


class ReportPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.role in MANAGERS or user.role == 'teacher'))

