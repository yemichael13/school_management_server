from rest_framework.permissions import BasePermission


class IsStudentManager(BasePermission):
    """School staff allowed to manage student records and history."""

    allowed_roles = frozenset({'admin', 'principal', 'kindergarten_principal', 'primary_principal', 'teacher'})

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.role in self.allowed_roles))
