"""
Custom exception handler for Study Vault API.
Ensures consistent error formatting with {"detail": "..."} across endpoints.
"""

from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first to get standard response
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data

        # If data is a dict, normalize so {"detail": "string"} is returned
        if isinstance(data, dict):
            if 'detail' in data:
                if isinstance(data['detail'], list) and len(data['detail']) > 0:
                    response.data['detail'] = str(data['detail'][0])
                else:
                    response.data['detail'] = str(data['detail'])
            elif 'non_field_errors' in data and data['non_field_errors']:
                err = data['non_field_errors'][0]
                response.data = {'detail': str(err)}
            elif len(data) == 1:
                key, val = next(iter(data.items()))
                if isinstance(val, list) and len(val) > 0:
                    response.data = {'detail': f"{key}: {val[0]}" if key != 'error' else str(val[0])}
                elif isinstance(val, str):
                    response.data = {'detail': val}
        elif isinstance(data, list) and len(data) > 0:
            response.data = {'detail': str(data[0])}

    return response
