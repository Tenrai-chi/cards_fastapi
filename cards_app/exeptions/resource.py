from cards_app.exeptions.base import AppException
from cards_app.utils.response_types import ResponseType


class ResourceException(AppException):
    """ Базовое для ошибок ресурсов пользователя """

    pass


class InsufficientFundsUserError(ResourceException):
    """
    Исключение, возникающее при недостатке средств у пользователя для действия.
    Возвращает статус ответа REDIRECT_WITH_ERROR.
    """

    def __init__(self, need_gold: int | None = None):
        """ Формирует сообщение об ошибке """

        message = f'У вас недостаточно средств: необходимо {need_gold}'
        super().__init__(message, response_type=ResponseType.REDIRECT_WITH_ERROR)
