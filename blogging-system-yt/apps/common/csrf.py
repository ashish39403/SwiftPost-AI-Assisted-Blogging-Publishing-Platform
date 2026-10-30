from django.http import JsonResponse


def csrf_failure(request, reason=""):
    return JsonResponse(
        {
            "error": {
                "code": "CSRF_FAILED",
                "message": "CSRF verification failed.",
                "details": {},
            }
        },
        status=403,
    )
