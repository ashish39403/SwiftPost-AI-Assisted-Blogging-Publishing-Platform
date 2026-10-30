from rest_framework.exceptions import APIException


class ProviderNotConfigured(APIException):
    status_code = 503
    default_detail = "That provider is not configured."
    api_code = "PROVIDER_NOT_CONFIGURED"


class ProviderUnavailable(APIException):
    status_code = 503
    default_detail = "The provider could not complete the request."
    api_code = "PROVIDER_UNAVAILABLE"


class ProviderBudgetExceeded(APIException):
    status_code = 429
    default_detail = "The search test budget has been used up."
    api_code = "PROVIDER_BUDGET_EXCEEDED"
