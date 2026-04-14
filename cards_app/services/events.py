import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.models import News

logger = logging.getLogger(__name__)


async def get_paginated_news(session: AsyncSession, limit: int, offset: int) -> list[News]:
    """ Возвращает список новостей с пагинацией, отсортированный по дате создания.
        Args:
            session: сессия базы данных
            limit: максимальное количество новостей в одной странице
            offset: сдвиг для пагинации

        Returns:
            list[News]: Список объектов News
    """

    stmt = (select(News)
            .order_by(News.date_time_create.desc())
            .limit(limit)
            .offset(offset))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_total_news_count(session: AsyncSession) -> int:
    """ Возвращает общее количество новостей для пагинации.
        Args:
            session: сессия базы данных

        Returns:
            int: общее число записей в таблице News.
    """

    stmt = select(func.count()).select_from(News)
    result = await session.execute(stmt)
    return result.scalar_one()
