from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from cards_app.models import Card, ClassCard, Rarity
from cards_app.models.exchange import AmuletItem


async def get_card_with_details(session_db: AsyncSession,
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
    result = await session_db.execute(stmt)
    return result.scalar_one_or_none()


async def get_drop_chance_card(session_db: AsyncSession) -> dict:
    """ Получение данных о шансе выпадения редкости карты """

    answer_data = {'rarities': None,
                   'classes': None}

    stmt_classes = select(ClassCard)
    result_classes = await session_db.execute(stmt_classes)
    all_classes = result_classes.scalars().all()
    answer_data['classes'] = all_classes

    stmt_rarities = select(Rarity)
    result_rarities = await session_db.execute(stmt_rarities)
    all_rarities = result_rarities.scalars().all()

    answer_data['rarities'] = all_rarities

    return answer_data
