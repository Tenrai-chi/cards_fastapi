import logging
from random import choices, choice

from collections import Counter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, contains_eager

from cards_app.exeptions import (BoxNotFoundError, ExpItemNotFoundError, AmuletNotFoundError, AmuletNotOnSaleError,
                                 UpgradeItemNotFoundError)
from cards_app.models import CardStore, Rarity, Boxes, AmuletType, UpgradeItemsType, ExperienceItems, User
from cards_app.services.cards import generate_max_stat_ur_card, create_record_in_history_receiving_card
from cards_app.services.inventory import (add_experience_books_batch, can_user_receive_amulet, give_amulets_to_user_butch,
                                          add_upgrade_item_to_user)
from cards_app.services.profile import check_can_user_receive_card, charge_user_gold, create_transaction

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
        .join(CardStore.rarity_card)
        .where(CardStore.sale_now == True)
        .options(
            # загружено в основном запросе для сортировки
            contains_eager(CardStore.rarity_card),
            joinedload(CardStore.type_card),
            joinedload(CardStore.class_card)
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
        .options(joinedload(AmuletType.rarity))
        .order_by(AmuletType.rarity_id.desc())
    )
    result = await session_db.execute(stmt_amulets)
    amulets = list(result.scalars().all())
    return amulets


async def get_amulet_by_name(session_db: AsyncSession, name: str) -> AmuletType:
    """ Получает тип амулета по его имени
        Args:
            session_db: сессия базы данных
            name: название амулета
        Returns:
            AmuletType: список амулетов, доступных к покупке
    """

    stmt_amulet = select(AmuletType).where(AmuletType.name == name)
    result = await session_db.execute(stmt_amulet)
    amulet = result.scalar_one_or_none()
    return amulet


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


async def get_box_info(session_db: AsyncSession, box_id: int) -> Boxes:
    """ Возвращает информацию о сундуке
        Args:
            session_db: сессия базы данных
            box_id: ID сундука
        Returns:
            Boxes: информация о сундуке
        Raises:
            BoxNotFoundError: если сундук не существует
    """

    result = await session_db.execute(select(Boxes).where(Boxes.id == box_id))
    box = result.scalar_one_or_none()
    if box is None:
        raise BoxNotFoundError
    return box


async def open_box_card(session_db: AsyncSession, user: User) -> int:
    """ Открытие сундука с картой.
        Проверяет, может ли пользователь получить награду из сундука.
        Запускает создание карты.
        Args:
            session_db: сессия базы данных
            user: User + Profile текущего пользователя
        Return:
            int: ID созданной карты
    """

    await check_can_user_receive_card(session_db=session_db,
                                      current_user=user,
                                      need_slots=1)
    new_card_id = await generate_max_stat_ur_card(session_db=session_db,
                                                  user_profile_id=user.profile.id)

    return new_card_id


async def open_box_exp_item(session_db: AsyncSession, user: User
                            ) -> list[ExperienceItems]:
    """ Открытие сундука с предметами опыта.
        Генерирует список из 10 книг, которые получит пользователь при открытии.
        Как минимум одна книга в списке будет UR редкости.
        Отправляет награду в инвентарь пользователя.
        Возвращает список созданных книг опыта.
        Args:
            session_db: сессия базы данных
            user: User + Profile текущего пользователя
        Returns:
            list[ExperienceItems]: список книг, полученных пользователем
    """

    stmt_all_books = select(ExperienceItems).order_by(ExperienceItems.rarity)
    result = await session_db.execute(stmt_all_books)
    all_books = result.scalars().all()

    book_by_rarity = {book.rarity: book for book in all_books}
    book_r, book_sr, book_ur = [book_by_rarity[rarity]
                                for rarity in ('R', 'SR', 'UR')]
    candidates = [book_r, book_sr, book_ur]
    weights = [book.chance_drop_on_box for book in candidates]
    reward_books = [book_ur]

    for _ in range(9):
        chosen = choices(candidates, weights=weights, k=1)[0]
        reward_books.append(chosen)

    counter = Counter(book.id for book in reward_books)
    await add_experience_books_batch(session_db=session_db,
                                     user_profile_id=user.profile.id,
                                     items_amount=dict(counter)
                                     )
    return reward_books


async def open_box_amulet(session_db: AsyncSession, user: User
                          ) -> list[AmuletType]:
    """ Открытие сундука с амулетами.
        Генерирует список из 5 амулетов, которые получит пользователь при открытии.
        Как минимум один амулет будет редкости UR.
        Отправляет награду в инвентарь пользователя.
        Возвращает список созданных книг опыта.
        Args:
            session_db: сессия базы данных
            user: User + Profile текущего пользователя
        Returns:
            list[AmuletType]: список амулетов полученных из сундука
    """

    await can_user_receive_amulet(session_db=session_db,
                                  current_user=user,
                                  need_slots=5)

    stmt_amulets = select(AmuletType).options(joinedload(AmuletType.rarity))
    result = await session_db.execute(stmt_amulets)
    all_amulets = result.scalars().all()

    amulets_by_rarity = {}
    for amulet in all_amulets:
        name = amulet.rarity.name
        amulets_by_rarity.setdefault(name, []).append(amulet)

    candidates_rarity = ['R', 'SR', 'UR']
    weights = []
    for rarity_name in candidates_rarity:
        sample = amulets_by_rarity.get(rarity_name)[0]
        if sample:
            weights.append(sample.rarity.chance_drop_on_box)

    ur_amulets = amulets_by_rarity.get('UR', [])
    first_amulet = choice(ur_amulets)
    reward_amulets = [first_amulet]

    for _ in range(4):
        chosen_rarity_name = choices(candidates_rarity, weights=weights, k=1)[0]
        available = amulets_by_rarity.get(chosen_rarity_name, [])
        chosen_amulet = choice(available)
        reward_amulets.append(chosen_amulet)

    amulets_amount = {amulet.id: 1 for amulet in reward_amulets}
    await give_amulets_to_user_butch(session_db, user.profile.id, amulets_amount)

    return reward_amulets


async def buy_exp_items(session_db: AsyncSession,
                        exp_item_id: int,
                        exp_item_amount: int,
                        user: User
                        ) -> int:
    """ Покупка книг в магазине предметов.
        Args:
            session_db: сессия базы данных
            exp_item_id: ID покупаемой книги
            exp_item_amount: количество покупаемых книг
            user: User + Profile текущего пользователя
        Returns:
            int: Количество золота необходимое для покупки
        Raises:
            ExpItemNotFoundError: если запрашивается покупка несуществующей книги
    """

    stmt_exp_item = select(ExperienceItems).where(ExperienceItems.id == exp_item_id).with_for_update()
    result = await session_db.execute(stmt_exp_item)
    exp_item = result.scalar_one_or_none()
    if exp_item is None:
        logger.warning(f'Попытка пользователя ID {user.id} купить несуществующую книгу опыта с ID {exp_item_id}')
        raise ExpItemNotFoundError()

    need_gold = exp_item.price * exp_item_amount

    await add_experience_books_batch(
        session_db=session_db,
        user_profile_id=user.profile.id,
        items_amount={exp_item_id: exp_item_amount}
    )
    return need_gold


async def buy_amulet(session_db: AsyncSession,
                     amulet_id: int,
                     user: User
                     ) -> int:
    """ Покупка амулета в магазине предметов.
        Args:
            session_db: сессия базы данных
            amulet_id: ID покупаемого амулета
            user: User + Profile текущего пользователя
        Returns:
            int: цена амулета при покупке
        Raises:
            AmuletNotFoundError: если запрашивается покупка несуществующего амулета
            AmuletNotOnSaleError: попытка купить амулет, который не продается
    """

    await can_user_receive_amulet(session_db=session_db,
                                  current_user=user,
                                  need_slots=1)

    stmt_amulet = select(AmuletType).where(AmuletType.id == amulet_id)
    result = await session_db.execute(stmt_amulet)
    amulet = result.scalar_one_or_none()
    if amulet is None:
        logger.warning(f'Пользователь ID {user.id} попытался купить несуществующий амулет ID {amulet_id}')
        raise AmuletNotFoundError()
    if not amulet.sale_now:
        logger.warning(f'Пользователь ID {user.id} попытался купить амулет '
                       f'ID {amulet_id}, который находится не в продаже')
        raise AmuletNotOnSaleError()

    await give_amulets_to_user_butch(session_db=session_db,
                                     owner_id=user.profile.id,
                                     amulets_amount={amulet.id: 1})
    return amulet.price


async def buy_upgrade_item(session_db: AsyncSession,
                           upgrade_item_id: int,
                           user: User
                           ) -> int:
    """ Покупка предмета усиления в магазине предметов.
        Args:
            session_db: сессия базы данных
            upgrade_item_id: ID предмета усиления
            user: User + Profile текущего пользователя
        Returns:
            int: цена покупки предмета усиления
        Raises:
            UpgradeItemNotFoundError: если запрашивается покупка несуществующего предмета усиления
    """

    stmt_upgrade_item = select(UpgradeItemsType).where(UpgradeItemsType.id == upgrade_item_id)
    result = await session_db.execute(stmt_upgrade_item)
    upgrade_item = result.scalar_one_or_none()
    if upgrade_item is None:
        logger.warning(f'Пользователь ID {user.id} попытался купить несуществующий'
                       f'предмет усиления ID {upgrade_item_id}')
        raise UpgradeItemNotFoundError()

    await add_upgrade_item_to_user(session_db=session_db,
                                   user_profile_id=user.profile.id,
                                   upgrade_item=upgrade_item)

    return upgrade_item.price


async def get_book_by_name(session_db: AsyncSession, book_name: str
                           ) -> ExperienceItems:
    """ Получить книгу опыта по ее названию.
        Args:
            session_db: сессия базы данных
            book_name: название книги
        Returns:
            ExperienceItems: книга опыта
    """

    stmt = select(ExperienceItems).where(ExperienceItems.name == book_name)
    result = await session_db.execute(stmt)
    book = result.scalar_one_or_none()
    return book
