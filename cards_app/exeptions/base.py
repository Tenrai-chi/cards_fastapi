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
