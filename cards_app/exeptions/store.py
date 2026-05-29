from .base import AppException


class StoreException(AppException):
    """ Базовое для ошибок магазина """
    pass


class CardInStoreNotFoundError(StoreException):
    """ Исключение, возникающее при попытке получить несуществующую карту в магазине.
        Возвращает HTTP статус 404 (Not Found)
    """

    def __init__(self, card_id: int | None = None):
        """ Формирует сообщение об ошибке """

        message = f'Карта с id={card_id} не найдена в магазине'
        super().__init__(message, status_code=404)


class CardNotOnSaleError(StoreException):
    """ Исключение, возникающее при попытке купить карту не в продаже.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете купить эту карту'
        super().__init__(message, status_code=400)


class BoxNotFoundError(StoreException):
    """ Исключение, возникающее при попытке получить несуществующий сундук.
        Возвращает HTTP статус 404 (Not Found)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете купить этот сундук'
        super().__init__(message, status_code=404)


class ExpItemNotFoundError(StoreException):
    """ Исключение, возникающее при попытке купить несуществующую книгу.
        Возвращает HTTP статус 404 (Not Found)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете купить эту книгу'
        super().__init__(message, status_code=404)


class AmuletNotFoundError(StoreException):
    """ Исключение, возникающее при попытке купить несуществующий амулет.
        Возвращает HTTP статус 404 (Not Found)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете купить этот амулет'
        super().__init__(message, status_code=404)


class AmuletNotOnSaleError(StoreException):
    """ Исключение, возникающее при попытке купить амулет не в продаже.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете купить этот амулет'
        super().__init__(message, status_code=400)


class UpgradeItemNotFoundError(StoreException):
    """ Исключение, возникающее при попытке купить несуществующий редмет усиления.
        Возвращает HTTP статус 404 (Not Found)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете купить этот предмет усиления'
        super().__init__(message, status_code=404)