from rest_framework.authentication import SessionAuthentication as DRFSessionAuthentication
from rest_framework.exceptions import PermissionDenied


class SessionAuthentication(DRFSessionAuthentication):
    """Cookie session auth for the separate Next.js app.

    Authenticated unsafe requests always require CSRF. Anonymous login and
    register also require CSRF. Other anonymous writes skip CSRF so the
    permission layer can return AUTHENTICATION_REQUIRED instead of CSRF_FAILED.
    """

    _anonymous_csrf_prefixes = ("/api/v1/auth/login", "/api/v1/auth/register")

    def authenticate(self, request):
        user = getattr(request._request, "user", None)
        if user and user.is_authenticated and user.is_active:
            self._enforce_csrf(request)
            return (user, None)
        if self._anonymous_needs_csrf(request):
            self._enforce_csrf(request)
        return None

    def authenticate_header(self, request):
        return "Session"

    def _anonymous_needs_csrf(self, request):
        path = request.path
        return any(path.startswith(prefix) for prefix in self._anonymous_csrf_prefixes)

    def _enforce_csrf(self, request):
        try:
            self.enforce_csrf(request)
        except PermissionDenied:
            denied = PermissionDenied("CSRF verification failed.")
            denied.api_code = "CSRF_FAILED"
            raise denied
