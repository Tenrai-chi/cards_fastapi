from .base import AppException


class FightException(AppException):
    """ Базовое для ошибок связанных с битвами """
    pass


class SelfFightError(FightException):
    """ Исключение, возникающее при попытке начать битву с самим собой.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете бросить вызов самому себе'
        super().__init__(message, status_code=400)

