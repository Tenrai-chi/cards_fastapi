from cards_app.utils.response_types import ResponseType

RESPONSE_TYPE_TO_HTTP = {
    ResponseType.SUCCESS: 200,
    ResponseType.REDIRECT_WITH_INFO: 303,
    ResponseType.REDIRECT_WITH_ERROR: 303,
    ResponseType.BAD_REQUEST: 400,
    ResponseType.UNAUTHORIZED: 401,
    ResponseType.FORBIDDEN: 403,
    ResponseType.NOT_FOUND: 404,
    ResponseType.SERVER_ERROR: 500,
}

TEMPLATE_FOR_STATUS = {
    401: 'errors/error_401.html',
    403: 'errors/error_403.html',
    404: 'errors/error_404.html',
    500: 'errors/error_500.html',
}


def get_error_template(status_code: int) -> str:
    """Возвращает имя шаблона для статуса ошибки."""
    return TEMPLATE_FOR_STATUS.get(status_code, 'errors/error_500.html')
