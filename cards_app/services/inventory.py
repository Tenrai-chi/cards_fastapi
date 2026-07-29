import logging
from random import randint, shuffle, choice

from sqlalchemy import select, func, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from cards_app.exeptions import (NotEnoughSlotsError, AmuletNotFoundError, NotAmuletOwnerError,
                                 NotEnoughUpgradeItemsError, CardNotFoundError, NotCardOwnerError, MaxUpgradeCardError)
from cards_app.models import (UsersInventory, ExperienceItems, User, AmuletItem, AmuletType, UpgradeItemsUsers, Card,
                              UpgradeItemsType)
from cards_app.services.cards import get_card_with_details
from cards_app.services.profile import charge_user_gold, create_transaction
from cards_app.types import RewardLootAfterFightDict

logger = logging.getLogger(__name__)


async def add_experience_books_batch(session_db: AsyncSession,
                                     user_profile_id: int,
                                     items_amount: dict[int, int]
                                     ) -> None:
    """ Добавляет книги опыта в инвентарь пользователя.
        Если у пользователя уже есть такой предмет – увеличивает количество,
        иначе создаёт новую запись.
        Args:
            session_db: сессия базы данных
            user_profile_id: ID Profile пользователя
            items_amount: словарь с ID типа книги и количеством
    """

    if not items_amount:
        logger.error(f'Принят пустой словарь в добавлении книг опыта в инвентарь пользователя')
        return

    stmt_inventory = (
        select(UsersInventory)
        .where(UsersInventory.owner_id == user_profile_id,
               UsersInventory.item_id.in_(items_amount.keys())
               )
        .with_for_update()
    )
    result_inventory = await session_db.execute(stmt_inventory)
    inventory_map = {inventory.item_id: inventory for inventory in result_inventory.scalars().all()}

    for item_id, add_amount in items_amount.items():
        if item_id in inventory_map:
            inventory_map[item_id].amount += add_amount
            session_db.add(inventory_map[item_id])
        else:
            new_inv = UsersInventory(owner_id=user_profile_id,
                                     item_id=item_id,
                                     amount=add_amount
                                     )
            session_db.add(new_inv)
    logger.info(f'Пользователь ID Profile {user_profile_id} получил книги')


async def add_upgrade_item_to_user(session_db: AsyncSession,
                                   user_profile_id: int,
                                   upgrade_item: UpgradeItemsType,
                                   ) -> None:
    """ Добавляет книги опыта в инвентарь пользователя.
        Если у пользователя уже есть такой предмет – увеличивает количество,
        иначе создаёт новую запись.
        Принимает в аргументах либо редкость, либо название книги
        Args:
            session_db: сессия базы данных
            user_profile_id: ID Profile пользователя
            upgrade_item: сущность предмета усиления
    """

    stmt_inv = (
        select(UpgradeItemsUsers)
        .where(
            UpgradeItemsUsers.owner_id == user_profile_id,
            UpgradeItemsUsers.upgrade_item_type_id == upgrade_item.id
        )
        .with_for_update()
    )
    inv_result = await session_db.execute(stmt_inv)
    inventory = inv_result.scalar_one_or_none()

    if inventory:
        inventory.amount += 1
        session_db.add(inventory)
    else:
        new_inventory = UpgradeItemsUsers(
            owner_id=user_profile_id,
            upgrade_item_type_id=upgrade_item.id,
            amount=1
        )
        session_db.add(new_inventory)
    logger.info(f'Пользователь ID Profile {user_profile_id} получил {upgrade_item.name}')


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

    stmt_count_amulets = (select(func.count())
                          .select_from(AmuletItem)
                          .where(AmuletItem.owner_id == current_user.profile.id)
                          )
    result = await session_db.execute(stmt_count_amulets)
    amulets_count = result.scalar_one()
    if need_slots > current_user.profile.amulet_slots - amulets_count:
        logger.warning(f'Пользователь ID {current_user.profile.id} пытается получить амулет, но не хватает слотов '
                       f'(нужно {need_slots}, свободно {current_user.profile.amulet_slots - amulets_count})')
        raise NotEnoughSlotsError('У вас недостаточно места для новых амулетов')


async def get_all_amulets_user(session_db: AsyncSession, owner_id: int
                               ) -> list[AmuletItem]:
    """ Возвращает список всех амулетов пользователя.
        Args:
            session_db: сессия базы данных
            owner_id: ID Profile владельца

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


async def give_amulets_to_user_butch(session_db: AsyncSession,
                                     owner_id: int,
                                     amulets_amount: dict[int, int]
                                     ) -> None:
    """ Создает в инвентарь пользователя амулет по названию амулета.
        Args:
            session_db: сессия базы данных
            owner_id: ID Profile пользователя
            amulets_amount: словарь с айди амулетов и количеством копий
    """

    if not amulets_amount:
        return

    values = []
    for amulet_type_id, quantity in amulets_amount.items():
        values.extend([
            {'amulet_type_id': amulet_type_id, 'owner_id': owner_id, 'card_id': None, 'upgrades': 0}
            for _ in range(quantity)
        ])

    await session_db.execute(insert(AmuletItem).values(values))
    logger.info(f'Пользователь Profile {owner_id} получил {sum(amulets_amount.values())} амулетов')


async def delete_amulet(session_db: AsyncSession,
                        owner_id: int,
                        amulet_id: int
                        ) -> int:
    """ Удаление амулета из инвентаря пользователя.
        Args:
            session_db: сессия базы данных
            owner_id: ID Profile пользователя, который запросил удаление
            amulet_id: ID амулета
        Returns:
            int: 50 % цены удаления (продажи)
        Raises:
            - AmuletNotFoundError: если такого амулета нет в базе данных
            - NotAmuletOwnerError: если пользователь не является владельцем
    """

    stmt_amulet = (select(AmuletItem)
                   .where(AmuletItem.id == amulet_id)
                   .options(selectinload(AmuletItem.amulet_type))
                   .with_for_update()
                   )
    result = await session_db.execute(stmt_amulet)
    amulet = result.scalar_one_or_none()
    if amulet is None:
        logger.warning(f'Амулет ID {amulet_id} не найден')
        raise AmuletNotFoundError()
    if amulet.owner_id != owner_id:
        logger.warning(f'Пользователь ID {owner_id} попытался удалить амулет ID {amulet_id}'
                       f'не являясь владельцем')
        raise NotAmuletOwnerError()
    if amulet.card_id:
        await remove_amulet_from_card(session_db=session_db,
                                      amulet=amulet)

    logger.info(f'Амулет ID {amulet.id} удален')
    price_for_sell = amulet.amulet_type.price // 2
    await session_db.delete(amulet)
    return price_for_sell


async def remove_amulet_from_card(session_db: AsyncSession,
                                  amulet: AmuletItem | None = None,
                                  card_id: int | None = None,
                                  ) -> None:
    """ Снятие амулета с карты
        Args:
            session_db: сессия базы данных
            amulet: Амулет (при необходимости)
            card_id: ID карты (при необходимости)
    """

    if amulet:
        amulet.card_id = None
        session_db.add(amulet)
        logger.info(f'Амулет ID {amulet.id} снят с карты')

    elif card_id:
        stmt_card = select(AmuletItem).where(AmuletItem.card_id == card_id)
        result = await session_db.execute(stmt_card)
        amulet = result.scalar_one_or_none()
        if amulet is None:
            return
        amulet.card_id = None
        session_db.add(amulet)
        logger.info(f'Амулет ID {amulet.id} снят с карты')


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
            buff_value: численное значение усиления, если карта пользователя класса Эльф
        Returns:
            RewardLootAfterFightDict:
                - amulets (list[AmuletType]):
                - exp_items (list[ExperienceItems]):
    """

    answer_data = {'exp_items': [],
                   'amulets': []}

    count_stmt = select(func.count()).select_from(AmuletItem).where(AmuletItem.owner_id == user.profile.id)
    count = (await session_db.execute(count_stmt)).scalar_one()
    free_slots = user.profile.amulet_slots - count
    new_amulets = []
    if free_slots > 0:
        # Создание списка для получения
        all_amulets: list = await get_all_types_amulets(session_db=session_db)
        shuffle(all_amulets)

        for amulet in all_amulets:
            if len(new_amulets) >= free_slots or len(new_amulets) == 2:
                break
            chance = randint(1, 100)
            base_chance_drop = amulet.rarity.chance_drop_on_fight
            if base_chance_drop == 0:
                continue
            chance_drop = amulet.rarity.chance_drop_on_fight + (buff_value or 0)
            if chance <= chance_drop:
                new_amulets.append(amulet)

        # Начисление амулетов
        if new_amulets:
            amulets_amount = {amulet.id: 1 for amulet in new_amulets}
            await give_amulets_to_user_butch(session_db=session_db,
                                             owner_id=user.profile.id,
                                             amulets_amount=amulets_amount)

    # Запускает получение книг опыта add_experience_books (по редкости)
    all_exp_items: list = await get_all_exp_items(session_db=session_db)
    books_counter = {}
    for item in all_exp_items:
        chance = randint(1, 100)
        chance_drop = item.chance_drop_on_fight + (buff_value or 0)
        if chance <= chance_drop:
            books_counter[item.id] = books_counter.get(item.id, 0) + 1
            answer_data['exp_items'].append(item)

    if books_counter:
        await add_experience_books_batch(session_db=session_db,
                                         user_profile_id=user.profile.id,
                                         items_amount=books_counter)

    answer_data['amulets'] = new_amulets

    return answer_data


async def get_all_types_amulets(session_db: AsyncSession) -> list[AmuletType]:
    """ Получает все типы амулетов с их редкостью
        Args:
            session_db: сессия базы данных
        Returns:
            list[AmuletType]: все существующие типы амулетов
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


async def get_exp_items_in_user_inventory(session_db: AsyncSession,
                                          owner_id: int
                                          ) -> list[UsersInventory]:
    """ Получает список книг опыта в инвентаре пользователя.
        Args:
            session_db: сессия базы данных
            owner_id: ID Profile пользователя
        Returns:
            list[UsersInventory]: список книг опыта
    """

    stmt_exp_items = (
        select(UsersInventory)
        .where(UsersInventory.owner_id == owner_id, UsersInventory.amount > 0)
        .options(selectinload(UsersInventory.item))
        .order_by(UsersInventory.item_id)
    )
    result = await session_db.execute(stmt_exp_items)
    exp_items = list(result.scalars().all())

    return exp_items


async def get_upgrade_items_in_user_inventory(session_db: AsyncSession,
                                              owner_id: int
                                              ) -> list[UpgradeItemsUsers]:
    """ Получает список предметов усиления в инвентаре пользователя.
        Args:
            session_db: сессия базы данных
            owner_id: ID Profile пользователя
        Returns:
            list[UpgradeItemsUsers]: список предметов усиления
    """

    stmt_upg_items = (
        select(UpgradeItemsUsers)
        .where(UpgradeItemsUsers.owner_id == owner_id)
        .options(joinedload(UpgradeItemsUsers.upgrade_item_type))
        .order_by(UpgradeItemsUsers.id)
    )
    result = await session_db.execute(stmt_upg_items)
    upg_items = list(result.scalars().all())
    return upg_items


async def get_upgrade_item_in_inventory(session_db: AsyncSession,
                                        upgrade_item_type_id: int,
                                        owner_id: int
                                        ) -> UpgradeItemsUsers:
    """ Получает предмет усиления из инвентаря пользователя.
        Args:
            session_db: сессия базы данных
            upgrade_item_type_id: ID типа предмета усиления
            owner_id: ID Profile пользователя запросившего усиление
        Returns:
            UpgradeItemsUsers: предмет усиления из инвентаря
    """

    stmt_upg_item = (
        select(UpgradeItemsUsers)
        .where(UpgradeItemsUsers.owner_id == owner_id,
               UpgradeItemsUsers.upgrade_item_type_id == upgrade_item_type_id)
        .options(joinedload(UpgradeItemsUsers.upgrade_item_type))
        .with_for_update(of=UpgradeItemsUsers)
    )
    result = await session_db.execute(stmt_upg_item)
    upg_item = result.scalar_one_or_none()
    return upg_item


async def get_amulets_in_user_inventory(session_db: AsyncSession,
                                        owner_id: int
                                        ) -> list[AmuletItem]:
    """ Получает список амулетов в инвентаре пользователя.
        Args:
            session_db: сессия базы данных
            owner_id: ID Profile пользователя
        Returns:
            list[AmuletItem]: список амулетов
    """

    stmt_amulets = (
        select(AmuletItem)
        .where(AmuletItem.owner_id == owner_id)
        .options(
            joinedload(AmuletItem.amulet_type).joinedload(AmuletType.rarity),
            joinedload(AmuletItem.card).joinedload(Card.class_card),
            joinedload(AmuletItem.card).joinedload(Card.rarity_card)
        )
        .order_by(AmuletItem.id)
    )
    result = await session_db.execute(stmt_amulets)
    amulets = list(result.scalars().all())
    return amulets


async def upgrade_card_stats_and_level(session_db: AsyncSession,
                                       card: Card,
                                       upgrade_item: UpgradeItemsUsers
                                       ) -> None:
    """ Обновляет характеристики карты в зависимости от предмета усиления.
        Args:
            session_db: сессия базы данных
            card: карта для усиления
            upgrade_item: предмет усиления
        Raises:
            ValueError: при неожиданном типе усиления (не должен вызываться, так как база целостная)
    """

    if upgrade_item.upgrade_item_type.type == 'random':
        if choice(['attack', 'hp']) == 'attack':
            card.damage += upgrade_item.upgrade_item_type.amount_up
        else:
            card.hp += upgrade_item.upgrade_item_type.amount_up

    elif upgrade_item.upgrade_item_type.type == 'attack':
        card.damage += upgrade_item.upgrade_item_type.amount_up

    elif upgrade_item.upgrade_item_type.type == 'hp':
        card.hp += upgrade_item.upgrade_item_type.amount_up

    else:
        logger.error(f'Получен неизвестный тип усиления: {upgrade_item.upgrade_item_type.type}')
        raise ValueError(f'Непредвиденный тип усиления')

    upgrade_item.amount -= 1
    if upgrade_item.amount <= 0:
        await session_db.delete(upgrade_item)
    else:
        session_db.add(upgrade_item)

    card.enhancement += 1
    session_db.add(card)


async def upgrade_card(session_db: AsyncSession,
                       card_id: int,
                       upgrade_item_id: int,
                       user: User
                       ) -> int:
    """ Использует предмет усиления на карте.
        Args:
            session_db: сессия базы данных
            card_id: ID карты
            upgrade_item_id: ID типа предмета усиления
            user: User + Profile пользователя
        Returns:
            int: Стоимость использоваения предмета усиления
        Raises:
            NotEnoughUpgradeItemsError: если предметов недостаточно
            NotCardOwnerError: пользователь не является владельцем карты
            CardNotFoundError: карты не существует
            MaxUpgradeCardError: карта уже имеет максимальный уровень усиления
    """

    upg_item = await get_upgrade_item_in_inventory(session_db=session_db,
                                                   upgrade_item_type_id=upgrade_item_id,
                                                   owner_id=user.profile.id)
    if upg_item is None or upg_item.amount < 1:
        logger.warning(f'У пользователя ID {user.id} недостаточно предметов усиления ID {upgrade_item_id}')
        raise NotEnoughUpgradeItemsError

    card = await get_card_with_details(session_db=session_db,
                                       card_id=card_id,
                                       for_update=True)
    if card is None:
        logger.warning(f'Карта ID {card_id} не найдена')
        raise CardNotFoundError

    if card.owner_id != user.profile.id:
        logger.warning(f'Пользователь ID {user.id} попытался усилить карту ID {card.id}, не являясь владельцем')
        raise NotCardOwnerError

    if card.enhancement >= card.max_enhancement:
        logger.warning(f'Пользователь ID {user.id} попытался усилить карту ID {card.id}, '
                       f'имеющую максимальный уровень усиления')
        raise MaxUpgradeCardError

    await upgrade_card_stats_and_level(session_db=session_db,
                                       card=card,
                                       upgrade_item=upg_item)

    return upg_item.upgrade_item_type.price_of_use
