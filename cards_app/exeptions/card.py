from .base import AppException


class CardException(AppException):
    """ Базовое для ошибок карт """
    pass


class CardNotFoundError(CardException):
    """ Исключение, возникающее при попытке получить несуществующую карту.
        Возвращает HTTP статус 404 (Not Found)
    """

    def __init__(self, card_id: int | None = None):
        """ Формирует сообщение об ошибке в зависимости от наличия card_id """

        message = f'Карта с id={card_id} не найдена' if card_id else 'Карта(ы) не найдена'
        super().__init__(message, status_code=404)


class NoCurrentCardError(CardException):
    """ Исключение, возникающее если у одного из участников не выбрана карта для боя.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self, username):
        """ Формирует сообщение об ошибке """

        message = f'У пользователя {username} нет избранной карты для боя'
        super().__init__(message, status_code=400)


class NotCardOwnerError(CardException):
    """ Исключение, если пользователь не является владельцем карты.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не являетесь владельцем этой карты'
        super().__init__(message, status_code=400)


class EmptyCardsForMergeError(CardException):
    """ Исключение, если список карт для слияния пуст.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Для слияния не были выбраны карты'
        super().__init__(message, status_code=400)


class TooManyCardsMergeError(CardException):
    """ Исключение, если список карт для слияния больше,
        чем необходимо для максимального уровня слияния.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Выбрано слишком много карт для слияния'
        super().__init__(message, status_code=400)


class MaxUpgradeCardError(CardException):
    """ Исключение, возникающее при попытке усилить карту,
        которая уже имеет максимальное усиление.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Эта карта уже имеет максимальный уровень усиления'
        super().__init__(message, status_code=400)


class SelfMergeError(CardException):
    """ Исключение, если список карт для слияния больше,
        чем необходимо для максимального уровня слияния.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'нельзя пожертвовать для слияния текущую карту'
        super().__init__(message, status_code=400)
