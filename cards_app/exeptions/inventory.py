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


class AmuletNotFoundError(InventoryException):
    """ Исключение, если амулет не найден.
        Возвращает HTTP статус 404 (Not Found)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Амулет не найден'
        super().__init__(message, status_code=404)


class NotAmuletOwnerError(InventoryException):
    """ Исключение, если пользователь не является владельцем амулета.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не являетесь владельцем этого амулета'
        super().__init__(message, status_code=400)
