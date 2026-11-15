from rest_framework.permissions import BasePermission


MANAGER_ROLES = frozenset({'admin', 'principal', 'kindergarten_principal', 'primary_principal'})


class IsTeacherManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.role in MANAGER_ROLES:
            return True
        return request.method in ('GET', 'HEAD', 'OPTIONS') and user.role == 'teacher'

