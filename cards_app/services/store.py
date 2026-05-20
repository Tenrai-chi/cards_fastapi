import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cards_app.models import CardStore, Rarity

logger = logging.getLogger(__name__)


async def get_cards_in_store(session_db: AsyncSession) -> list[CardStore]:
    """ Возвращает список карт, доступных для покупки в магазине.
        Args:
            session_db: сессия базы данных

        Returns:
            list[CardStore]: Список карт-шаблонов, у которых sale_now == True.
            Каждый объект содержит подгруженные атрибуты:
                - rarity_card (Rarity)
                - type_card (Type)
                - class_card (ClassCard)
    """

    stmt_cards = (
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
    result = await session_db.execute(stmt_cards)
    cards = list(result.scalars().all())
    return cards
