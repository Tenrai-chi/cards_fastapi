from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from cards_app.models.users import RefreshToken


async def store_refresh_token(db: AsyncSession, user_id: int, token: str, expires_at: datetime) -> RefreshToken:
    """ Создает новый refresh-токен для сессии пользователя """

    db_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token


async def get_refresh_token(db: AsyncSession, token: str) -> RefreshToken | None:
    """ Проверяет refresh-токен на наличие в базе данных """

    result = await db.execute(select(RefreshToken).where(RefreshToken.token == token))
    return result.scalar_one_or_none()


async def delete_refresh_token(db: AsyncSession, token: str) -> None:
    """ Удаляет refresh-токен из базы данных """

    db_token = await get_refresh_token(db, token)
    if db_token:
        await db.delete(db_token)
        await db.commit()
