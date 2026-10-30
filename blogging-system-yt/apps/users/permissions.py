from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from apps.accounts.models import Role
from apps.accounts.permissions import authentication_required


class HasRole(BasePermission):
    required_roles = ()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            raise authentication_required()
        if user.role not in self.required_roles:
            raise PermissionDenied("You do not have permission to do that.")
        return True


class IsReader(HasRole):
    required_roles = (Role.READER, Role.AUTHOR, Role.ADMIN)


class IsAuthor(HasRole):
    required_roles = (Role.AUTHOR, Role.ADMIN)


class IsAdmin(HasRole):
    required_roles = (Role.ADMIN,)


class IsOwner(BasePermission):
    """Object access for the owning account. Product admins are a separate check."""

    owner_attr = "author"

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            raise authentication_required()
        if user.role == Role.ADMIN:
            return True
        owner = getattr(obj, self.owner_attr)
        return owner == user
