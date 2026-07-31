from cards_app.utils.response_types import ResponseType


class AppException(Exception):
    """
    Базовое исключение для всех бизнес-ошибок приложения.
    Attributes:
        message (str): Текст ошибки.
        response_type (str): тип ответа.
    """

    def __init__(self, message: str, response_type: ResponseType):
        """ Инициализирует базовое исключение """

        self.message = message
        self.response_type = response_type
        super().__init__(message)
