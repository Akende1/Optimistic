import logging
from functools import lru_cache

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, OperationalError, ProgrammingError, connection
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


logger = logging.getLogger(__name__)
GENERIC_API_ERROR = 'The request could not be completed right now. Please try again shortly.'
SCHEMA_DRIFT_ERROR = 'Database schema is out of date. Run "python manage.py migrate" and reload the server.'


def is_schema_drift_error(exc):
    current = exc
    while current is not None:
        if isinstance(current, (OperationalError, ProgrammingError)):
            message = str(current).lower()
            if 'no such column' in message or 'has no column named' in message or 'no such table' in message:
                return True
        current = getattr(current, '__cause__', None)
    return False


@lru_cache(maxsize=128)
def db_column_exists(table_name, column_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return any(col.name == column_name for col in description)


def model_field_available(model, field_name):
    field = model._meta.get_field(field_name)
    return db_column_exists(model._meta.db_table, field.column)


def schema_drift_response(response_cls=Response):
    return response_cls(
        {
            'error': 'Database schema out of date',
            'detail': SCHEMA_DRIFT_ERROR,
        },
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def get_user_related_instance(user, *relation_names):
    if not user or not getattr(user, 'is_authenticated', False):
        return None

    for relation_name in relation_names:
        try:
            return getattr(user, relation_name)
        except (AttributeError, ObjectDoesNotExist):
            continue
        except DatabaseError:
            if is_schema_drift_error(__import__('sys').exc_info()[1]):
                logger.warning('Schema drift while resolving user relation %s for user %s', relation_name, getattr(user, 'pk', None))
            else:
                logger.exception('Failed to resolve user relation %s for user %s', relation_name, getattr(user, 'pk', None))
            return None
        except Exception:
            logger.exception('Unexpected error resolving user relation %s for user %s', relation_name, getattr(user, 'pk', None))
            return None

    return None


def get_user_seller(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return None

    try:
        from apps.sellers.models import Seller

        if not model_field_available(Seller, 'primary_location'):
            return Seller.objects.only(
                'id', 'user', 'store_name', 'phone', 'description',
                'profile_image', 'banner_image', 'verified', 'created_at'
            ).get(user=user)
    except ObjectDoesNotExist:
        return None
    except DatabaseError as exc:
        if is_schema_drift_error(exc):
            logger.warning('Schema drift while resolving seller for user %s', getattr(user, 'pk', None))
            return None
        logger.exception('Failed to resolve seller for user %s', getattr(user, 'pk', None))
        return None

    return get_user_related_instance(user, 'seller')


def get_user_delivery_partner(user):
    return get_user_related_instance(user, 'delivery_partner', 'delivery_partner_profile')


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        if isinstance(response.data, dict):
            if 'error' not in response.data:
                detail = response.data.get('detail')
                response.data = {
                    'error': detail if isinstance(detail, str) else 'Request failed',
                    'details': response.data,
                }
        else:
            response.data = {
                'error': 'Request failed',
                'details': response.data,
            }
        return response

    if is_schema_drift_error(exc):
        request = context.get('request')
        logger.warning(
            'Schema drift detected for %s %s',
            getattr(request, 'method', 'UNKNOWN'),
            getattr(request, 'path', 'UNKNOWN'),
        )
        return schema_drift_response()

    request = context.get('request')
    logger.exception(
        'Unhandled API exception for %s %s',
        getattr(request, 'method', 'UNKNOWN'),
        getattr(request, 'path', 'UNKNOWN'),
        exc_info=exc,
    )
    return Response(
        {
            'error': 'Internal server error',
            'detail': GENERIC_API_ERROR,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


class ApiExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as exc:
            if not request.path.startswith('/api/'):
                raise

            if is_schema_drift_error(exc):
                logger.warning('Schema drift detected in middleware for %s %s', request.method, request.path)
                return schema_drift_response(JsonResponse)

            logger.exception(
                'Unhandled middleware exception for %s %s',
                request.method,
                request.path,
            )
            return JsonResponse(
                {
                    'error': 'Internal server error',
                    'detail': GENERIC_API_ERROR,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )