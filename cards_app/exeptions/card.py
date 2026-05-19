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

        message = f'Карта с id={card_id} не найдена' if card_id else 'Карта не найдена'
        super().__init__(message, status_code=404)


class NoCurrentCardError(CardException):
    """ Исключение, возникающее если у одного из участников не выбрана карта для боя.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self, username):
        """ Формирует сообщение об ошибке """

        message = f'У пользователя {username} нет избранной карты для боя'
        super().__init__(message, status_code=400)
