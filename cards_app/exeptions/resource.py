from .base import AppException


class ResourceException(AppException):
    """ Базовое для ошибок ресурсов пользователя """
    pass


class InsufficientFundsUserError(ResourceException):
    """ Исключение, возникающее при недостатке средств у пользователя для действия.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self, need_gold: int | None = None):
        """ Формирует сообщение об ошибке """

        message = f'У вас недостаточно средств: необходимо {need_gold}'
        super().__init__(message, status_code=400)