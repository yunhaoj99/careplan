import logging

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .exceptions import BaseAppException

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    # Our own exceptions — we fully control the format
    if isinstance(exc, BaseAppException):
        return Response(exc.to_dict(), status=exc.http_status)

    # Django ORM's DoesNotExist → 404
    if isinstance(exc, ObjectDoesNotExist):
        return Response(
            {
                'type': 'error',
                'code': 'NOT_FOUND',
                'message': str(exc) or 'Resource not found',
            },
            status=404,
        )

    # DRF's ValidationError (raised by serializer.is_valid(raise_exception=True))
    if isinstance(exc, DRFValidationError):
        return Response(
            {
                'type': 'validation_error',
                'code': 'VALIDATION_ERROR',
                'message': 'Validation failed',
                'detail': exc.detail,
            },
            status=400,
        )

    # Let DRF handle everything else (404, 405, auth errors, etc.)
    response = drf_exception_handler(exc, context)
    if response is not None:
        response.data = {
            'type': 'error',
            'code': getattr(exc, 'default_code', 'ERROR'),
            'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
        }
        return response

    # Truly unexpected — log it, never expose internals
    logger.exception("Unhandled exception", exc_info=exc)
    return Response(
        {
            'type': 'error',
            'code': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred. Please try again.',
        },
        status=500,
    )
