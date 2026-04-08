from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.models import News


async def get_paginated_news(session: AsyncSession, limit: int, offset: int) -> list[News]:
    """Возвращает список новостей с пагинацией, отсортированный по дате (сначала новые)"""

    stmt = (select(News)
            .order_by(News.date_time_create.desc())
            .limit(limit)
            .offset(offset))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_total_news_count(session: AsyncSession) -> int:
    """Возвращает общее количество новостей для пагинации"""

    stmt = select(func.count()).select_from(News)
    result = await session.execute(stmt)
    return result.scalar_one()
