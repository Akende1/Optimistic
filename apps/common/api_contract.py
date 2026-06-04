from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import exception_handler


def success_response(data=None, status_code=200, **extra_fields):
    payload = {'success': True, 'data': data}
    payload.update(extra_fields)
    return Response(payload, status=status_code)


class StandardPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'pagination': {
                'page': self.page.number,
                'page_size': self.get_page_size(self.request),
                'total_pages': self.page.paginator.num_pages,
            }
        })


def _extract_error_message(detail):
    if isinstance(detail, dict):
        for key in ('error', 'detail', 'message'):
            if key in detail and detail[key]:
                value = detail[key]
                if isinstance(value, list):
                    return str(value[0])
                return str(value)
        first_value = next(iter(detail.values()), 'Request failed')
        if isinstance(first_value, list):
            return str(first_value[0])
        return str(first_value)
    if isinstance(detail, list) and detail:
        return str(detail[0])
    return str(detail or 'Request failed')


def standardized_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    detail = response.data
    message = _extract_error_message(detail)
    code = getattr(exc, 'default_code', None)

    response.data = {
        'success': False,
        'error': {
            'message': message,
            'code': code,
            'details': detail,
        }
    }
    return response
