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
    """ Исключение, возникающее при попытке получить несуществующего пользователя """

    def __init__(self, user_id: int | None = None):
        """ Формирует сообщение об ошибке в зависимости от наличия user_id """

        message = f'Пользователь с id={user_id} не найден' if user_id else 'Пользователь не найден'
        super().__init__(message, status_code=404)


class CardNotFoundError(AppException):
    """ Исключение, возникающее при попытке получить несуществующую карту """

    def __init__(self, card_id: int | None = None):
        """ Формирует сообщение об ошибке в зависимости от наличия card_id """

        message = f'Карта с id={card_id} не найдена' if card_id else 'Карта не найдена'
        super().__init__(message, status_code=404)


class CardInStoreNotFoundError(AppException):
    """ Исключение, возникающее при попытке получить несуществующую карту в магазине """

    def __init__(self, card_id: int | None = None):
        """ Формирует сообщение об ошибке """

        message = f'Карта с id={card_id} не найдена в магазине'
        super().__init__(message, status_code=404)


class InsufficientFundsUserError(AppException):
    """ Исключение, возникающее при недостатке средств у пользователя для действия """

    def __init__(self, need_gold: int | None = None):
        """ Формирует сообщение об ошибке """

        message = f'У вас недостаточно средств: необходимо {need_gold}'
        super().__init__(message, status_code=404)


class NotEnoughSlotsError(AppException):
    """ Исключение, возникающее при недостатке слотов в инвентаре.
        Применимо к картам, амулетам, гильдиям, избранным пользователям
    """

    def __init__(self, message: str | None = None):
        """ Формирует сообщение об ошибке """

        super().__init__(message, status_code=404)


class CardNotOnSaleError(AppException):
    """ Исключение, возникающее при попытке купить карту не в продаже """

    def __init__(self):
        """ Формирует сообщение об ошибке """
        message = f'Вы не можете купить эту карту'
        super().__init__(message, status_code=404)

