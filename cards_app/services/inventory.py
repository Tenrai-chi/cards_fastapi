import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.exeptions import NotEnoughSlotsError
from cards_app.models import UsersInventory, ExperienceItems, User, AmuletItem, AmuletType

logger = logging.getLogger(__name__)


async def add_experience_book(session_db: AsyncSession,
                              user_id: int,
                              amount: int,
                              rarity_book: str = None,
                              name_book: str = None
                              ) -> None:
    """ Добавляет книги опыта в инвентарь пользователя.
        Если у пользователя уже есть такой предмет – увеличивает количество,
        иначе создаёт новую запись.
        Принимает в аргументах либо редкость, либо название книги
        Args:
            session_db: сессия базы данных
            user_id: ID профиля пользователя
            amount: количество
            rarity_book: редкость книги
            name_book: название книги
    """

    if name_book:
        stmt_item = select(ExperienceItems).where(ExperienceItems.name == name_book)
    else:
        stmt_item = select(ExperienceItems).where(ExperienceItems.rarity == rarity_book)
    result = await session_db.execute(stmt_item)
    item = result.scalar_one_or_none()

    stmt_inv = select(UsersInventory).where(
        UsersInventory.owner_id == user_id,
        UsersInventory.item_id == item.id
    )
    inv_result = await session_db.execute(stmt_inv)
    inventory = inv_result.scalar_one_or_none()

    if inventory:
        inventory.amount += amount
        session_db.add(inventory)
    else:
        new_inventory = UsersInventory(
            owner_id=user_id,
            item_id=item.id,
            amount=amount
        )
        session_db.add(new_inventory)


async def can_user_receive_amulet(session_db: AsyncSession,
                                        current_user: User,
                                        need_slots: int) -> None:
    """ Проверяет, хватит ли у пользователя места в инвентаре для новых амулетов.
        Args:
            session_db: сессия базы данных
            current_user: объект User текущего пользователя
            need_slots: количество слотов, необходимых для новых амулетов
        Raises:
            NotEnoughSlotsError: если свободных слотов меньше, чем необходимо
    """

    all_amulets = await get_all_amulets_user(session_db, current_user.profile.id)
    if need_slots > current_user.profile.amulet_slots - len(all_amulets):
        logger.warning(f'Пользователь ID {current_user.profile.id} пытается получить амулет, но не хватает слотов '
                       f'(нужно {need_slots}, свободно {current_user.profile.card_slots - len(all_amulets)})')
        raise NotEnoughSlotsError('У вас недостаточно места для новых амулетов')


async def get_all_amulets_user(session_db: AsyncSession,
                               owner_id: int
                               ) -> List[AmuletItem]:

    """ Возвращает список всех амулетов пользователя.
        Args:
            session_db: сессия базы данных
            owner_id: ID профиля владельца

        Returns:
            List[AmuletItem]: список амулетов, принадлежащих пользователю
    """

    stmt = select(AmuletItem).where(AmuletItem.owner_id == owner_id).order_by(AmuletItem.amulet_type_id)
    result = await session_db.execute(stmt)
    amulets = list(result.scalars().all())
    return amulets


async def give_amulet_to_user(session_db: AsyncSession,
                              owner_id: int,
                              name_amulet: str):
    """ Создает в инвентарь пользователя амулет по имени.
        Args:
            session_db: сессия базы данных
            owner_id: ID профиля пользователя
            name_amulet: название амулета
    """

    stmt = select(AmuletType).where(AmuletType.name == name_amulet)
    result = await session_db.execute(stmt)
    amulet_type = result.scalar_one_or_none()

    new_amulet_item = AmuletItem(amulet_type_id=amulet_type.id,
                                 owner_id=owner_id,
                                 card_id=None,
                                 upgrades=0
                                 )
    session_db.add(new_amulet_item)
