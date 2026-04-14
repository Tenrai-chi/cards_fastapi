class AppException(Exception):
    """ Базовое исключение для всех бизнес-ошибок приложения.

        Attributes:
            message (str): Текст ошибки
            status_code (int): HTTP-статус, по умолчанию 400
    """

    def __init__(self, message: str, status_code: int = 400):
        """ Инициализирует базовое исключение """

        self.message = message
        self.status_code = status_code
        super().__init__(message)


class UserNotFoundError(AppException):
    """ Исключение, возникающее при попытке получить несуществующего пользователя.
        Возвращает HTTP статус 404 (Not Found)
    """

    def __init__(self, user_id: int | None = None):
        """ Формирует сообщение об ошибке в зависимости от наличия user_id """

        message = f'Пользователь ID: {user_id} не найден' if user_id else 'Пользователь не найден'
        super().__init__(message, status_code=404)


class SelfFavoriteError(AppException):
    """ Исключение, возникающее при попытке пользователя добавить в избранное самого себя.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете добавить в избранное самого себя'
        super().__init__(message, status_code=400)


class SelfFavoriteRemoveError(AppException):
    """ Исключение, возникающее при попытке пользователя удалить из избранного самого себя.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете удалить из избранного самого себя'
        super().__init__(message, status_code=400)


class DuplicateFavoriteError(AppException):
    """ Исключение, возникающее при попытке добавить в избранное пользователя,
        который уже присутствует в списке избранных текущего пользователя.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Этот пользователь уже находится в списке избранных'
        super().__init__(message, status_code=400)


class FavoriteNotFoundError(AppException):
    """ Исключение, возникающее при попытке удалить из избранного пользователя, которого там не было.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Этот пользователь не находится в вашем списке избранных'
        super().__init__(message, status_code=400)


class CardNotFoundError(AppException):
    """ Исключение, возникающее при попытке получить несуществующую карту.
        Возвращает HTTP статус 404 (Not Found)
    """

    def __init__(self, card_id: int | None = None):
        """ Формирует сообщение об ошибке в зависимости от наличия card_id """

        message = f'Карта с id={card_id} не найдена' if card_id else 'Карта не найдена'
        super().__init__(message, status_code=404)


class CardInStoreNotFoundError(AppException):
    """ Исключение, возникающее при попытке получить несуществующую карту в магазине.
        Возвращает HTTP статус 404 (Not Found)
    """

    def __init__(self, card_id: int | None = None):
        """ Формирует сообщение об ошибке """

        message = f'Карта с id={card_id} не найдена в магазине'
        super().__init__(message, status_code=404)


class InsufficientFundsUserError(AppException):
    """ Исключение, возникающее при недостатке средств у пользователя для действия.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self, need_gold: int | None = None):
        """ Формирует сообщение об ошибке """

        message = f'У вас недостаточно средств: необходимо {need_gold}'
        super().__init__(message, status_code=400)


class NotEnoughSlotsError(AppException):
    """ Исключение, возникающее при недостатке слотов в инвентаре.
        Применимо к картам, амулетам, гильдиям, избранным пользователям.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self, message: str):
        """ Формирует сообщение об ошибке """

        super().__init__(message, status_code=400)


class CardNotOnSaleError(AppException):
    """ Исключение, возникающее при попытке купить карту не в продаже.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете купить эту карту'
        super().__init__(message, status_code=400)

