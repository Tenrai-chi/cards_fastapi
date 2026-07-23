from cards_app.exeptions.base import AppException
from cards_app.utils.response_types import ResponseType


class InventoryException(AppException):
    """ Базовое для ошибок связанных с инвентарем пользователя """
    pass


class NotEnoughSlotsError(InventoryException):
    """ Исключение, возникающее при недостатке слотов в инвентаре.
        Применимо к картам, амулетам, гильдиям, избранным пользователям.
        Возвращает статус ответа REDIRECT_WITH_ERROR.
    """

    def __init__(self, message: str):
        """ Формирует сообщение об ошибке """

        super().__init__(message, response_type=ResponseType.REDIRECT_WITH_ERROR)


class AmuletNotFoundError(InventoryException):
    """ Исключение, если амулет не найден.
        Возвращает статус ответа NOT_FOUND.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Амулет не найден'
        super().__init__(message, response_type=ResponseType.NOT_FOUND)


class NotAmuletOwnerError(InventoryException):
    """ Исключение, если пользователь не является владельцем амулета.
        Возвращает статус ответа FORBIDDEN.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не являетесь владельцем этого амулета'
        super().__init__(message, response_type=ResponseType.FORBIDDEN)


class NotEnoughUpgradeItemsError(InventoryException):
    """ Исключение, возникающее при недостатке предметов усиления в инвентаре.
        Возвращает статус ответа REDIRECT_WITH_ERROR.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'У вас недостаточно предметов усиления'
        super().__init__(message, response_type=ResponseType.REDIRECT_WITH_ERROR)
