import logging

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from cards_app.config.database import get_db_session
from cards_app.config.security import decode_token
from cards_app.models.users import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login', auto_error=False)


logger = logging.getLogger(__name__)


def _get_token_from_request(request: Request, token: str | None = None) -> str | None:
    """ Получает токен из заголовка или куки.
        Приоритет: заголовок Authorization, затем cookie 'access_token'.
    """

    if not token:
        token = request.cookies.get('access_token')
    return token


async def get_current_user_id(request: Request,
                              token: str = Depends(oauth2_scheme),
                              ) -> int | None:
    """ Зависимость для POST-запросов.
        Возвращает ID текущего пользователя или None, если не авторизован.
    """

    token = _get_token_from_request(request, token)
    if not token:
        return None

    payload = decode_token(token, expected_type='access')
    if not payload:
        return None

    user_id = payload.get('sub')
    if not user_id:
        return None

    try:
        return int(user_id)
    except (ValueError, TypeError):
        logger.warning(f'Получен невалидный user_id: {user_id}')
        return None


async def get_current_user_with_profile(request: Request,
                                        token: str = Depends(oauth2_scheme),
                                        db: AsyncSession = Depends(get_db_session)) -> User | None:
    """ Зависимость для GET-запросов.
        Получает текущего пользователя или None, если он не авторизован
    """

    token = _get_token_from_request(request, token)
    if not token:
        return None

    payload = decode_token(token, expected_type='access')
    if not payload:
        return None

    user_id = payload.get('sub')
    if not user_id:
        return None

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        logger.warning(f'Получен невалидный user_id: {user_id}')
        return None

    result = await db.execute(select(User)
                              .where(User.id == int(user_id))
                              .options(joinedload(User.profile))
                              )
    user = result.scalar_one_or_none()

    if not user:
        return None
    if not user.is_active:
        raise HTTPException(status_code=403, detail='Пользователь заблокирован')
    return user
