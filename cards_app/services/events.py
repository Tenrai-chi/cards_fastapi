import logging

from datetime import date, datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.models import News, InitialEventAwards, User

logger = logging.getLogger(__name__)


async def get_paginated_news(session_db: AsyncSession, limit: int, offset: int) -> list[News]:
    """ Возвращает список новостей с пагинацией, отсортированный по дате создания.
        Args:
            session_db: сессия базы данных
            limit: максимальное количество новостей в одной странице
            offset: сдвиг для пагинации

        Returns:
            list[News]: Список объектов News
    """

    stmt = (select(News)
            .order_by(News.date_time_create.desc())
            .limit(limit)
            .offset(offset))
    result = await session_db.execute(stmt)
    return list(result.scalars().all())


async def get_total_news_count(session_db: AsyncSession) -> int:
    """ Возвращает общее количество новостей для пагинации.
        Args:
            session_db: сессия базы данных

        Returns:
            int: общее число записей в таблице News.
    """

    stmt = select(func.count()).select_from(News)
    result = await session_db.execute(stmt)
    return result.scalar_one()


async def get_info_start_event_awards(session_db: AsyncSession) -> list[InitialEventAwards]:
    """ Возвращает список наград стартового события.
        Args:
            session_db: сессия базы данных
        Returns:
            list[InitialEventAwards]: Список наград (объектов) InitialEventAwards
    """

    stmt = (select(InitialEventAwards)
            .order_by(InitialEventAwards.day_event_visit.asc()))
    result = await session_db.execute(stmt)
    return list(result.scalars().all())


async def can_get_start_event_award(user: User) -> bool:
    """ Проверяет, что пользователь может получить награду стартового события.
        Args:
            user: объект пользователя
        Returns:
            bool: True, если пользователь может получить награду
    """

    if user.profile.event_visit >= 30:
        return False

    if user.profile.date_event_visit is None:
        return True

    today = date.today()
    day_passed = user.profile.date_event_visit < today
    return bool(day_passed)


async def update_profile_event_award_received(session_db: AsyncSession,
                                              user: User
                                              ) -> None:
    """ Обновляет информацию в профиле пользователя при получении награды.
        Args:
            session_db: сессия базы данных
            user: объект пользователя
    """

    user.profile.event_visit += 1
    user.profile.date_event_visit = datetime.now()
    session_db.add(user)


async def get_info_award(session_db: AsyncSession,
                         day_visit: int
                         ) -> InitialEventAwards:
    """ Получает запись награды по дню.
        Args:
            session_db: сессия базы данных
            day_visit: день получения награды
        Returns:
            InitialEventAwards: награда этого дня
    """

    stmt = select(InitialEventAwards).where(InitialEventAwards.day_event_visit == day_visit)
    result = await session_db.execute(stmt)
    return result.scalar_one_or_none()
