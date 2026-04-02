from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from cards_app.models import Card
from cards_app.models.exchange import AmuletItem


async def get_card_with_details(session: AsyncSession,
                                card_id: int
                                ) -> Card | None:
    """ Возвращает карту с подгруженными амулетом, классом, типом и редкостью """
    stmt = (
        select(Card)
        .where(Card.id == card_id)
        .options(
            selectinload(Card.class_card),
            selectinload(Card.rarity_card),
            selectinload(Card.type_card),
            selectinload(Card.amulet).selectinload(AmuletItem.amulet_type)
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
