from cards_app.exeptions.base import AppException
from cards_app.utils.response_types import ResponseType


class StoreException(AppException):
    """ Базовое для ошибок магазина """
    pass


class CardInStoreNotFoundError(StoreException):
    """ Исключение, возникающее при попытке получить несуществующую карту в магазине.
        Возвращает статус ответа NOT_FOUND.
    """

    def __init__(self, card_id: int | None = None):
        """ Формирует сообщение об ошибке """

        message = f'Карта с id={card_id} не найдена в магазине'
        super().__init__(message, response_type=ResponseType.NOT_FOUND)


class CardNotOnSaleError(StoreException):
    """ Исключение, возникающее при попытке купить карту не в продаже.
        Возвращает статус ответа REDIRECT_WITH_ERROR.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете купить эту карту'
        super().__init__(message, response_type=ResponseType.REDIRECT_WITH_ERROR)


class BoxNotFoundError(StoreException):
    """ Исключение, возникающее при попытке получить несуществующий сундук.
        Возвращает статус ответа NOT_FOUND.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете купить этот сундук'
        super().__init__(message, response_type=ResponseType.NOT_FOUND)


class ExpItemNotFoundError(StoreException):
    """ Исключение, возникающее при попытке купить несуществующую книгу.
        Возвращает статус ответа NOT_FOUND.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете купить эту книгу'
        super().__init__(message, response_type=ResponseType.NOT_FOUND)


class AmuletNotFoundError(StoreException):
    """ Исключение, возникающее при попытке купить несуществующий амулет.
        Возвращает статус ответа NOT_FOUND.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете купить этот амулет'
        super().__init__(message, response_type=ResponseType.NOT_FOUND)


class AmuletNotOnSaleError(StoreException):
    """ Исключение, возникающее при попытке купить амулет не в продаже.
        Возвращает статус ответа REDIRECT_WITH_ERROR.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете купить этот амулет'
        super().__init__(message, response_type=ResponseType.REDIRECT_WITH_ERROR)


class UpgradeItemNotFoundError(StoreException):
    """ Исключение, возникающее при попытке купить несуществующий предмет усиления.
        Возвращает статус ответа NOT_FOUND.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете купить этот предмет усиления'
        super().__init__(message, response_type=ResponseType.NOT_FOUND)
