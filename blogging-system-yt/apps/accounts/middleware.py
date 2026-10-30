import re

from django.conf import settings

SESSION_HEADER = "X-Session-Key"
_SESSION_KEY = re.compile(r"^[0-9a-zA-Z]{16,64}$")


class TabSessionMiddleware:
    """Let each browser tab keep its own Django session.

    The Next.js client stores the session key in sessionStorage and sends it as
    X-Session-Key. That value wins over the shared session cookie for the
    current request, so login or logout in another tab does not take over this one.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = (request.headers.get(SESSION_HEADER) or "").strip()
        if incoming and _SESSION_KEY.fullmatch(incoming):
            cookies = request.COOKIES.copy()
            cookies[settings.SESSION_COOKIE_NAME] = incoming
            request.COOKIES = cookies
        response = self.get_response(request)
        session = getattr(request, "session", None)
        key = getattr(session, "session_key", None) if session is not None else None
        if key:
            response[SESSION_HEADER] = key
        return response
