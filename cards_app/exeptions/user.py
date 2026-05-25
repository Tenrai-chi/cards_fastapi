from .base import AppException


class UserException(AppException):
    """ Базовое для ошибок пользователей """
    pass


class UserNotFoundError(UserException):
    """ Исключение, возникающее при попытке получить несуществующего пользователя.
        Возвращает HTTP статус 404 (Not Found)
    """

    def __init__(self, user_id: int | None = None):
        """ Формирует сообщение об ошибке в зависимости от наличия user_id """

        message = f'Пользователь ID: {user_id} не найден' if user_id else 'Пользователь не найден'
        super().__init__(message=message, status_code=404)


class CooldownNotElapsedError(UserException):
    """ Исключение возникающее при попытке действия, если не прошло необходимое время.
        Принимает готовое сообщение или количество необходимых (недостающих)
        часов для действия
        Если не передан ни один параметр, используется базовое сообщение.
        Возвращает HTTP статус 400 (Bad Request)
     """

    def __init__(self, base_message: str | None = None, hours: int | None = None):
        if hours and hours > 0:
            if hours == 1:
                hour_str = '1 час'
            elif 2 <= hours <= 4:
                hour_str = f'{hours} часа'
            else:
                hour_str = f'{hours} часов'
            time_part = f'Осталось {hour_str}'
        else:
            time_part = ''

        print(base_message, hours)
        if base_message:
            message = f'{base_message}. {time_part}' if time_part else base_message
        else:
            # Без base_message: стандартная фраза
            if hours > 0:
                message = f'Для данного действия необходимо подождать {hours}'
            else:
                message = 'Пока что вы не можете сделать это'
        super().__init__(message=message, status_code=400)


class UserFavoriteException(UserException):
    """ Базовое для ошибок избранного """
    pass


class SelfFavoriteError(UserFavoriteException):
    """ Исключение, возникающее при попытке пользователя добавить в избранное самого себя.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете добавить в избранное самого себя'
        super().__init__(message=message, status_code=400)


class SelfFavoriteRemoveError(UserFavoriteException):
    """ Исключение, возникающее при попытке пользователя удалить из избранного самого себя.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Вы не можете удалить из избранного самого себя'
        super().__init__(message=message, status_code=400)


class DuplicateFavoriteError(UserFavoriteException):
    """ Исключение, возникающее при попытке добавить в избранное пользователя,
        который уже присутствует в списке избранных текущего пользователя.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Этот пользователь уже находится в списке избранных'
        super().__init__(message=message, status_code=400)


class FavoriteNotFoundError(UserFavoriteException):
    """ Исключение, возникающее при попытке удалить из избранного пользователя, которого там не было.
        Возвращает HTTP статус 400 (Bad Request)
    """

    def __init__(self):
        """ Формирует сообщение об ошибке """

        message = f'Этот пользователь не находится в вашем списке избранных'
        super().__init__(message=message, status_code=400)
