from rest_framework.permissions import BasePermission


ACADEMIC_MANAGER_ROLES = frozenset({'admin', 'principal', 'kindergarten_principal', 'primary_principal'})
ACADEMIC_VIEWER_ROLES = ACADEMIC_MANAGER_ROLES | frozenset({'teacher'})


class AcademicRolePermission(BasePermission):
    allowed_roles = frozenset()

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.role in self.allowed_roles))


class IsAcademicManager(AcademicRolePermission):
    allowed_roles = ACADEMIC_MANAGER_ROLES


class IsAcademicViewer(AcademicRolePermission):
    allowed_roles = ACADEMIC_VIEWER_ROLES


class IsAcademicManagerOrReadOnly(IsAcademicManager):
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return IsAcademicViewer().has_permission(request, view)
        return super().has_permission(request, view)
