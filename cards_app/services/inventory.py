import logging
from random import randint, shuffle

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cards_app.exeptions import NotEnoughSlotsError
from cards_app.models import UsersInventory, ExperienceItems, User, AmuletItem, AmuletType
from cards_app.types import RewardLootAfterFightDict

logger = logging.getLogger(__name__)


async def add_experience_book(session_db: AsyncSession,
                              user_profile_id: int,
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
            user_profile_id: ID профиля пользователя
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
        UsersInventory.owner_id == user_profile_id,
        UsersInventory.item_id == item.id
    )
    inv_result = await session_db.execute(stmt_inv)
    inventory = inv_result.scalar_one_or_none()

    if inventory:
        inventory.amount += amount
        session_db.add(inventory)
        logger.info(f'Пользователь ID Profile {user_profile_id} получил {name_book or rarity_book}')
    else:
        new_inventory = UsersInventory(
            owner_id=user_profile_id,
            item_id=item.id,
            amount=amount
        )
        session_db.add(new_inventory)
        logger.info(f'Пользователь ID Profile {user_profile_id} получил книгу {name_book or rarity_book}')


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


async def get_all_amulets_user(session_db: AsyncSession, owner_id: int
                               ) -> list[AmuletItem]:

    """ Возвращает список всех амулетов пользователя.
        Args:
            session_db: сессия базы данных
            owner_id: ID профиля владельца

        Returns:
            list[AmuletItem]: список амулетов, принадлежащих пользователю
    """

    stmt_amulets = (
        select(AmuletItem)
        .where(AmuletItem.owner_id == owner_id)
        .order_by(AmuletItem.amulet_type_id)
    )
    result = await session_db.execute(stmt_amulets)
    amulets = list(result.scalars().all())
    return amulets


async def give_amulet_to_user(session_db: AsyncSession,
                              owner_id: int,
                              name_amulet: str) -> None:
    """ Создает в инвентарь пользователя амулет по названию амулета.
        Args:
            session_db: сессия базы данных
            owner_id: ID профиля пользователя
            name_amulet: название амулета
    """

    stmt_amulet = select(AmuletType).where(AmuletType.name == name_amulet)
    result = await session_db.execute(stmt_amulet)
    amulet_type = result.scalar_one_or_none()

    new_amulet_item = AmuletItem(amulet_type_id=amulet_type.id,
                                 owner_id=owner_id,
                                 card_id=None,
                                 upgrades=0
                                 )
    session_db.add(new_amulet_item)
    logger.info(f'Пользователь ID Profile {owner_id} получил амулет "{name_amulet}"')


async def reward_loot_after_fight(session_db: AsyncSession,
                                  user: User,
                                  buff_value: int | None = None
                                  ) -> RewardLootAfterFightDict:
    """ Выпадение книг опытов и амулетов после боя.
        Книги выпадают по одной на редкость.
        Максимум амулетов можно получить 2.
        Args:
            session_db: сессия базы данных
            user: User + Profile пользователя
            buff_value: численное значение бафа, если карта пользователя класса Эльф
        Returns:
            RewardLootAfterFightDict:
                - amulets (list[AmuletType]):
                - exp_items (list[ExperienceItems]):
    """

    answer_data = {'exp_items': [],
                   'amulets': []}
    # Вычисляет сколько амулетов может получить пользователь
    all_amulets_user = await get_all_amulets_user(session_db=session_db,
                                                  owner_id=user.profile.id)
    free_amulet_slots = user.profile.amulet_slots - len(all_amulets_user)
    new_amulets = []
    if free_amulet_slots > 0:
        # Создание списка для получения
        all_amulets: list = await get_all_types_amulets(session_db=session_db)
        shuffle(all_amulets)

        for amulet in all_amulets:
            if len(new_amulets) >= free_amulet_slots or len(new_amulets) == 2:
                break
            chance = randint(1, 100)
            base_chance_drop = amulet.rarity.chance_drop_on_fight
            if base_chance_drop == 0:
                continue
            chance_drop = amulet.rarity.chance_drop_on_fight + (buff_value or 0)
            if chance <= chance_drop:
                new_amulets.append(amulet)

        # Начисление амулетов
        for amulet in new_amulets:
            await give_amulet_to_user(session_db=session_db,
                                      owner_id=user.profile.id,
                                      name_amulet=amulet.name)

    # Запускает получение книг опыта add_experience_book (по редкости)
    all_exp_items: list = await get_all_exp_items(session_db=session_db)
    new_exp_items = []
    for item in all_exp_items:
        chance = randint(1, 100)
        chance_drop = item.chance_drop_on_fight + (buff_value or 0)
        if chance <= chance_drop:
            new_exp_items.append(item)

    for new_item in new_exp_items:
        await add_experience_book(session_db=session_db,
                                  user_profile_id=user.profile.id,
                                  amount=1,
                                  name_book=new_item.name,
                                  )
    answer_data['amulets'] = new_amulets
    answer_data['exp_items'] = new_exp_items

    return answer_data


async def get_all_types_amulets(session_db: AsyncSession) -> list[AmuletType]:
    """ Получает все типы амулетов с их редкостью
        Args:
            session_db: сессия базы данных
        Returns:
            list: из всех существующих типов амулетов
    """

    stmt_amulets = select(AmuletType).options(selectinload(AmuletType.rarity))
    result = await session_db.execute(stmt_amulets)
    amulets = list(result.scalars().all())
    return amulets


async def get_all_exp_items(session_db: AsyncSession) -> list[ExperienceItems]:
    """ Получает все типы книг опыта.
        Args:
            session_db: сессия базы данных
        Returns:
            list: из всех существующих типов книг опыта
    """

    stmt_exp_items = select(ExperienceItems)
    result = await session_db.execute(stmt_exp_items)
    exp_items = list(result.scalars().all())
    return exp_items
