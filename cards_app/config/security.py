from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext

from cards_app.config.settings import settings

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_moscow_time() -> datetime:
    """ Возвращает текущее московское время (UTC+3) """

    return datetime.now(timezone(timedelta(hours=3)))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ Проверяет соответствие пароля после хэширования и хэш-пароля в бд """

    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """ Возвращает хешированный пароль """

    return pwd_context.hash(password)


def create_access_token(user_id: int) -> str:
    """ Создает и возвращает JWT access-токен с маленьким сроком жизни. """

    expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        'sub': str(user_id),
        'exp': expire,
        'type': 'access'
    }
    return jwt.encode(payload, settings.SECRET_KEY_FOR_HASH, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """ Создает и возвращает JWT refresh-токен с большим сроком жизни.
        Используется для получения новой пары токенов (access+refresh) без повторного ввода пароля.
    """

    expire = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        'sub': str(user_id),
        'exp': expire,
        'type': 'refresh'
    }
    return jwt.encode(payload, settings.SECRET_KEY_FOR_HASH, algorithm=settings.ALGORITHM)


def decode_token(token: str, expected_type: str) -> dict | None:
    """ Декодирует и проверяет JWT токен.
        Расшифровывает токен, проверяет подпись, срок действия и тип.
        Используется в защищенных эндпоинтах.
    """

    try:
        payload = jwt.decode(token, settings.SECRET_KEY_FOR_HASH, algorithms=[settings.ALGORITHM])
        if payload.get('type') != expected_type:
            return None
        return payload
    except JWTError:
        return None
