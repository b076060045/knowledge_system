from django.http import JsonResponse
from knowledge_system.errors import KMsystemError, KMsystemException

from functools import wraps

def try_catch_decorator(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KMsystemException as e:
            return e.to_json()
        except Exception as e:
            error_message = repr(e)
            return KMsystemError.to_json_response(
                KMsystemError.INTERNAL_SERVER_ERROR,
                message=error_message
            )
    return decorator
