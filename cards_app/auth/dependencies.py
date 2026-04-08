from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cards_app.config.database import get_db_session
from cards_app.config.security import decode_token
from cards_app.models.users import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login', auto_error=False)


async def get_current_user_with_profile(request: Request,
                                        token: str = Depends(oauth2_scheme),
                                        db: AsyncSession = Depends(get_db_session)) -> User | None:
    """ Получение текущего пользователя или None, если он не авторизован """

    if not token:
        token = request.cookies.get('access_token')
    if not token:
        return None
    payload = decode_token(token, expected_type='access')
    if not payload:
        return None
    user_id = payload.get('sub')
    if not user_id:
        return None

    result = await db.execute(select(User)
                              .where(User.id == int(user_id))
                              .options(selectinload(User.profile)))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not user.is_active:
        raise HTTPException(status_code=403, detail='Пользователь заблокирован')
    return user
