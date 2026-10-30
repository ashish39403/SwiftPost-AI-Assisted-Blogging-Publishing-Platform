from rest_framework.response import Response
from rest_framework.views import exception_handler

_STATUS_CODES = {
    400: "VALIDATION_ERROR",
    401: "AUTHENTICATION_REQUIRED",
    403: "PERMISSION_DENIED",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    429: "RATE_LIMITED",
}


def api_exception_handler(exc, context):
    """Return one JSON error shape for every API failure.

    Field details are included for validation errors. Unexpected failures do not
    include exception text, SQL, or stack traces.
    """
    response = exception_handler(exc, context)
    if response is None:
        return Response(
            {
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "Something went wrong.",
                    "details": {},
                }
            },
            status=500,
        )

    code = getattr(exc, "api_code", None) or _STATUS_CODES.get(
        response.status_code, "REQUEST_FAILED"
    )
    message = "Request failed."
    details = {}
    data = response.data

    if isinstance(data, dict) and set(data.keys()) == {"detail"}:
        message = str(data["detail"])
    elif isinstance(data, dict):
        message = "The request was invalid."
        details = _stringify(data)
    elif isinstance(data, list):
        message = "The request was invalid."
        details = {"non_field_errors": _stringify(data)}

    response.data = {"error": {"code": code, "message": message, "details": details}}
    return response


def _stringify(value):
    if isinstance(value, dict):
        return {str(key): _stringify(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_stringify(item) for item in value]
    return str(value)
