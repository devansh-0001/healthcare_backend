import logging
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "A conflict occurred with an existing resource."
    default_code = "conflict"


def custom_exception_handler(exc, context):
    """
    Standardized DRF Exception Handler.
    Ensures all error responses conform to:
    {
        "error": {
            "code": "validation_error",
            "message": "Invalid input",
            "details": { ... }
        }
    }
    """
    response = exception_handler(exc, context)

    # In case of unhandled server exception (500)
    if response is None:
        logger.exception("Unhandled server exception: %s", exc, exc_info=True)
        return Response(
            {
                "error": {
                    "code": "server_error",
                    "message": "An unexpected error occurred on the server.",
                    "details": None,
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    status_code = response.status_code
    data = response.data

    code_map = {
        400: "validation_error",
        401: "authentication_failed",
        403: "permission_denied",
        404: "not_found",
        409: "conflict",
        429: "throttled",
        405: "method_not_allowed",
    }
    code = getattr(exc, "default_code", code_map.get(status_code, "error"))
    if hasattr(exc, "detail") and hasattr(exc.detail, "code") and exc.detail.code:
        code = str(exc.detail.code)
    elif status_code in code_map:
        code = code_map[status_code]

    message = "An error occurred."
    details = {}

    if isinstance(data, dict):
        if "detail" in data:
            message = str(data["detail"])
            # If there are other fields, keep them in details
            other_fields = {k: v for k, v in data.items() if k != "detail"}
            details = other_fields if other_fields else None
        else:
            message = "Invalid input" if status_code == 400 else "Request failed"
            details = data
    elif isinstance(data, list):
        if status_code == 400:
            message = "Validation failed for provided items."
        else:
            message = "Request failed."
        details = {"non_field_errors": data}
    else:
        message = str(data)
        details = None

    response.data = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }

    return response
