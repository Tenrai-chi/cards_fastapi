import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cards_app.models import CardStore, Rarity, Boxes, AmuletType, UpgradeItemsType, ExperienceItems

logger = logging.getLogger(__name__)


async def get_cards_in_store(session_db: AsyncSession) -> list[CardStore]:
    """ Возвращает список карт, доступных для покупки в магазине.
        Args:
            session_db: сессия базы данных
        Returns:
            list[CardStore]: список карт-шаблонов, у которых sale_now == True.
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


async def get_box_in_store(session_db: AsyncSession) -> list[Boxes]:
    """ Возвращает список сундуков, доступных для покупки в магазине.
        Args:
            session_db: сессия базы данных
        Returns:
            list[Boxes]: список сундуков, доступных к покупке
    """

    result_boxes = await session_db.execute(select(Boxes))
    boxes = list(result_boxes.scalars().all())
    return boxes


async def get_amulets_in_store(session_db: AsyncSession) -> list[AmuletType]:
    """ Возвращает список амулетов, доступных для покупки в магазине.
        Args:
            session_db: сессия базы данных
        Returns:
            list[AmuletType]: список амулетов, доступных к покупке
    """

    stmt_amulets = (
        select(AmuletType)
        .where(AmuletType.sale_now == True)
        .options(selectinload(AmuletType.rarity))
        .order_by(AmuletType.rarity_id.desc())
    )
    result = await session_db.execute(stmt_amulets)
    amulets = list(result.scalars().all())
    return amulets


async def get_upgrade_items_in_store(session_db: AsyncSession) -> list[UpgradeItemsType]:
    """ Возвращает список предметов усиления, доступных для покупки в магазине
        Args:
            session_db: сессия базы данных
        Returns:
            list[UpgradeItemsType]: список предметов усиления, доступных к покупке
    """

    result_upgrade_items = await session_db.execute(select(UpgradeItemsType))
    upgrade_items = list(result_upgrade_items.scalars().all())
    return upgrade_items


async def get_exp_items_in_store(session_db: AsyncSession) -> list[ExperienceItems]:
    """ Возвращает список книг опыта, доступных для покупки в магазине
        Args:
            session_db: сессия базы данных
        Returns:
            list[ExperienceItems]: список книг опыта, доступных к покупке
    """

    result_exp_items = await session_db.execute(select(ExperienceItems))
    exp_items = list(result_exp_items.scalars().all())
    return exp_items





