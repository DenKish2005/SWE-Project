from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    response.data = {
        "error": {
            "type": exc.__class__.__name__,
            "detail": response.data,
        }
    }
    return response
