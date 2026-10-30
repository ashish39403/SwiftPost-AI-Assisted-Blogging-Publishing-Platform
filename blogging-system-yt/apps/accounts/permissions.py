from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


def authentication_required():
    exc = AuthenticationFailed("Authentication is required.")
    exc.api_code = "AUTHENTICATION_REQUIRED"
    return exc


class IsAuthenticatedAccount(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user and user.is_authenticated and user.is_active:
            return True
        raise authentication_required()
