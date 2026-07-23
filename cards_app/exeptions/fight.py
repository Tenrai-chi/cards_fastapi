from cards_app.exeptions.base import AppException
from cards_app.utils.response_types import ResponseType


class FightException(AppException):
    """ Базовое для ошибок связанных с битвами """
    pass


class SelfFightError(FightException):
    """ Исключение, возникающее при попытке начать битву с самим собой.
        Возвращает статус ответа REDIRECT_WITH_ERROR.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете бросить вызов самому себе'
        super().__init__(message, response_type=ResponseType.REDIRECT_WITH_ERROR)

