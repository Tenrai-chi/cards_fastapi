from cards_app.exeptions.base import AppException
from cards_app.utils.response_types import ResponseType


class CardException(AppException):
    """ Базовое для ошибок карт """
    pass


class CardNotFoundError(CardException):
    """ Исключение, возникающее при попытке получить несуществующую карту.
        Возвращает статус ответа NOT_FOUND.
    """

    def __init__(self, card_id: int | None = None):
        """ Формирует сообщение об ошибке в зависимости от наличия card_id """

        message = f'Карта с id={card_id} не найдена' if card_id else 'Карта(ы) не найдена'
        super().__init__(message, response_type=ResponseType.NOT_FOUND)


class NoCurrentCardError(CardException):
    """ Исключение, возникающее если у одного из участников не выбрана карта для боя.
        Возвращает статус ответа REDIRECT_WITH_ERROR.
    """

    def __init__(self, username):
        """ Формирует сообщение об ошибке """

        message = f'У пользователя {username} нет избранной карты для боя'
        super().__init__(message, response_type=ResponseType.REDIRECT_WITH_ERROR)


class NotCardOwnerError(CardException):
    """ Исключение, если пользователь не является владельцем карты.
        Возвращает статус ответа FORBIDDEN.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не являетесь владельцем этой карты'
        super().__init__(message, response_type=ResponseType.FORBIDDEN)


class EmptyCardsForMergeError(CardException):
    """ Исключение, если список карт для слияния пуст.
        Возвращает статус ответа BAD_REQUEST.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Для слияния не были выбраны карты'
        super().__init__(message, response_type=ResponseType.BAD_REQUEST)


class TooManyCardsMergeError(CardException):
    """ Исключение, если список карт для слияния больше,
        чем необходимо для максимального уровня слияния.
        Возвращает статус ответа REDIRECT_WITH_ERROR.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Выбрано слишком много карт для слияния'
        super().__init__(message, response_type=ResponseType.REDIRECT_WITH_ERROR)


class MaxUpgradeCardError(CardException):
    """ Исключение, возникающее при попытке усилить карту,
        которая уже имеет максимальное усиление.
        Возвращает статус ответа REDIRECT_WITH_ERROR.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Эта карта уже имеет максимальный уровень усиления'
        super().__init__(message, response_type=ResponseType.REDIRECT_WITH_ERROR)


class SelfMergeError(CardException):
    """ Исключение, если была попытка слить саму себя.
        Возвращает статус ответа REDIRECT_WITH_ERROR.
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Нельзя пожертвовать для слияния текущую карту'
        super().__init__(message, response_type=ResponseType.REDIRECT_WITH_ERROR)
