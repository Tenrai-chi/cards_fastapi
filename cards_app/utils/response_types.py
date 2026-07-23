from enum import Enum


class ResponseType(str, Enum):
    """ Статусы ответов из Use Case для роутеров """

    SUCCESS = 'success'
    REDIRECT_WITH_ERROR = 'redirect_error'
    REDIRECT_WITH_INFO = 'redirect_info'
    BAD_REQUEST = 'bad_request'
    NOT_FOUND = 'not_found'
    FORBIDDEN = 'forbidden'
    UNAUTHORIZED = 'unauthorized'
    SERVER_ERROR = 'server_error'

