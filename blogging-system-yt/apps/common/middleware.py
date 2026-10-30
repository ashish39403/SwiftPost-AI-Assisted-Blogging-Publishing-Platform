class ApiSlashMiddleware:
    """Next's proxy forwards /api routes without a trailing slash."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/") and not request.path.endswith("/"):
            request.path_info = f"{request.path_info}/"
            request.path = f"{request.path}/"
        return self.get_response(request)
