import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from cards_app.schemas.base import CurrentUserForMenu
from cards_app.models.users import User, Profile

logger = logging.getLogger(__name__)


async def user_info_to_dto(user: User | None) -> CurrentUserForMenu | None:
    """
    Преобразует данные из User + Profile в DTO для вывода информации в шапку сайта
    Args:
        user: User + Profile или None, если не авторизирован.

    Returns:
        CurrentUserForMenu | None: DTO для вывода информации в шапку сайта
    """

    if user:
        current_user_dto = CurrentUserForMenu(
            id=user.id,
            username=user.username,
            gold=user.profile.gold,
            diamond=user.profile.diamond,
        )
        return current_user_dto


async def get_user_with_profile(session_db: AsyncSession, user_id: int) -> User | None:
    """
    Получение пользователя и его профиля (чтение)
    Args:
        session_db: сессия базы данных
        user_id: ID пользователя
    Returns:
        User | None: объект пользователя с загруженным Profile или None
    """

    stmt_user = (
        select(User)
        .where(User.id == user_id)
        .options(joinedload(User.profile))
    )

    result = await session_db.execute(stmt_user)
    user = result.scalar_one_or_none()

    return user


async def get_profile_for_update(session_db: AsyncSession, user_id: int) -> Profile | None:
    """
    Получение профиля с блокировкой транзакции, чтобы избежать ситуации race condition
    Args:
        session_db: сессия базы данных
        user_id: ID User текущего пользователя
    """

    stmt_profile = (
        select(Profile)
        .where(Profile.user_id == user_id)
        .with_for_update()
    )
    result = await session_db.execute(stmt_profile)
    profile = result.scalar_one_or_none()

    return profile
