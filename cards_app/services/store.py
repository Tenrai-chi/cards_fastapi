from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cards_app.models import CardStore, Rarity


async def get_cards_in_store(session_db: AsyncSession) -> list[CardStore]:
    """ Возвращает список новостей с пагинацией, отсортированный по дате (сначала новые) """

    stmt = (
        select(CardStore)
        .where(CardStore.sale_now == True)
        .join(CardStore.rarity_card)
        .options(
            selectinload(CardStore.rarity_card),
            selectinload(CardStore.type_card),
            selectinload(CardStore.class_card)
        )
        .order_by(Rarity.name.desc())
    )
    result = await session_db.execute(stmt)
    return list(result.scalars().all())
