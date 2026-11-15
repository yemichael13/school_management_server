from rest_framework.permissions import BasePermission

class RolePermission(BasePermission):
    allowed_roles = frozenset()
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.role in self.allowed_roles))
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)

class IsAdmin(RolePermission):
    allowed_roles = frozenset({'admin'})

class IsPrincipal(RolePermission):
    allowed_roles = frozenset({'principal', 'kindergarten_principal', 'primary_principal'})

class IsTeacher(RolePermission):
    allowed_roles = frozenset({'teacher'})

class IsStudent(RolePermission):
    allowed_roles = frozenset({'student'})

class IsAdminOrPrincipal(RolePermission):
    allowed_roles = frozenset({'admin', 'principal', 'kindergarten_principal', 'primary_principal'})

class IsTeacherOrPrincipal(RolePermission):
    allowed_roles = frozenset({'teacher', 'principal', 'kindergarten_principal', 'primary_principal'})

class IsKindergartenPrincipal(RolePermission):
    allowed_roles = frozenset({'kindergarten_principal'})
    def has_permission(self, request, view):
        if super().has_permission(request, view):
            return True
        if not request.user.is_authenticated or request.user.role != 'principal':
            return False
        return request.user.school_memberships.filter(is_active=True, role='principal', principal_scopes__school_level__code='kindergarten').exists()

class IsPrimaryPrincipal(RolePermission):
    allowed_roles = frozenset({'primary_principal'})
    def has_permission(self, request, view):
        if super().has_permission(request, view):
            return True
        if not request.user.is_authenticated or request.user.role != 'principal':
            return False
        return request.user.school_memberships.filter(is_active=True, role='principal', principal_scopes__school_level__code='primary').exists()
