from .base import AppException


class InventoryException(AppException):
    """ Базовое для ошибок связанных с инвентарем пользователя """
    pass


class NotEnoughSlotsError(InventoryException):
    """ Исключение, возникающее при недостатке слотов в инвентаре.
        Применимо к картам, амулетам, гильдиям, избранным пользователям.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self, message: str):
        """ Формирует сообщение об ошибке """

        super().__init__(message, status_code=400)