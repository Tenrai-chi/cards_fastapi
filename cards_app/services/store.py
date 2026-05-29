import logging
from random import choices, randint, choice

from collections import Counter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cards_app.exeptions import BoxNotFoundError, ExpItemNotFoundError, AmuletNotFoundError, AmuletNotOnSaleError, \
    UpgradeItemNotFoundError
from cards_app.models import CardStore, Rarity, Boxes, AmuletType, UpgradeItemsType, ExperienceItems, User, AmuletRarity
from cards_app.services.cards import generate_max_stat_ur_card, create_record_in_history_receiving_card
from cards_app.services.inventory import add_experience_book, can_user_receive_amulet, give_amulet_to_user, \
    add_upgrade_item_to_user
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
        Запускает создание записи о получении карты
        Args:
            session_db: сессия базы данных
            user: User + Profile
        Return:
            int: ID созданной карты
    """

    await check_can_user_receive_card(session_db=session_db,
                                      current_user=user,
                                      need_slots=1)
    new_card_id = await generate_max_stat_ur_card(session_db=session_db,
                                                  user_profile_id=user.profile.id)
    await create_record_in_history_receiving_card(session_db=session_db,
                                                  card_id=new_card_id,
                                                  user_profile_id=user.profile.id,
                                                  method_receiving=f'Открытие сундука')

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
            user: User + Profile
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
    for book_id, count in counter.items():
        book = next(book for book in all_books if book.id == book_id)
        await add_experience_book(session_db=session_db,
                                  user_profile_id=user.profile.id,
                                  amount=count,
                                  book=book
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
            user: User + Profile
        Returns:
            list[AmuletType]: список амулетов полученных из сундука
    """

    await can_user_receive_amulet(session_db=session_db,
                                  current_user=user,
                                  need_slots=5)

    stmt_amulets = select(AmuletType).options(selectinload(AmuletType.rarity))
    result = await session_db.execute(stmt_amulets)
    all_amulets = result.scalars().all()

    amulets_by_rarity = {}
    for amulet in all_amulets:
        name = amulet.rarity.name
        amulets_by_rarity.setdefault(name, []).append(amulet)

    stmt_rarities = select(AmuletRarity).where(AmuletRarity.name.in_(['R', 'SR', 'UR']))
    result = await session_db.execute(stmt_rarities)
    rarities = {r.name: r for r in result.scalars().all()}

    candidates_rarity = ['R', 'SR', 'UR']
    weights = [rarities[r].chance_drop_on_box for r in candidates_rarity]

    ur_amulets = amulets_by_rarity.get('UR', [])
    first_amulet = choice(ur_amulets)
    reward_amulets = [first_amulet]

    for _ in range(4):
        # Выбираем редкость по весам
        chosen_rarity_name = choices(candidates_rarity, weights=weights, k=1)[0]
        available = amulets_by_rarity.get(chosen_rarity_name, [])
        chosen_amulet = choice(available)
        reward_amulets.append(chosen_amulet)

    for amulet in reward_amulets:
        await give_amulet_to_user(session_db=session_db,
                                  owner_id=user.profile.id,
                                  amulet=amulet
                                  )

    return reward_amulets


async def buy_exp_items(session_db: AsyncSession,
                        exp_item_id: int,
                        exp_item_amount: int,
                        user: User
                        ) -> None:
    """ Покупка книг в магазине предметов.
        Args:
            session_db: сессия базы данных
            exp_item_id: ID покупаемой книги
            exp_item_amount: количество покупаемых книг
            user: User + Profile
        Raises:
            ExpItemNotFoundError: если запрашивается покупка несуществующей книги
    """

    stmt_exp_item = select(ExperienceItems).where(ExperienceItems.id == exp_item_id)
    result = await session_db.execute(stmt_exp_item)
    exp_item = result.scalar_one_or_none()
    if exp_item is None:
        raise ExpItemNotFoundError()

    need_gold = exp_item.price * exp_item_amount
    gold_transaction = await charge_user_gold(session_db=session_db,
                                              current_user=user,
                                              need_gold=need_gold)
    await create_transaction(session_db=session_db,
                             user_profile_id=user.profile.id,
                             gold_before=gold_transaction['gold_before'],
                             gold_after=gold_transaction['gold_after'],
                             comment=f'Покупка книг опыта в магазине')

    await add_experience_book(session_db=session_db,
                              user_profile_id=user.profile.id,
                              amount=exp_item_amount,
                              book=exp_item)


async def buy_amulet(session_db: AsyncSession,
                     amulet_id: int,
                     user: User
                     ) -> None:
    """ Покупка книг в магазине предметов.
        Args:
            session_db: сессия базы данных
            amulet_id: ID покупаемого амулета
            user: User + Profile
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
        raise AmuletNotFoundError()
    if not amulet.sale_now:
        raise AmuletNotOnSaleError()

    gold_transaction = await charge_user_gold(session_db=session_db,
                                              current_user=user,
                                              need_gold=amulet.price)
    await create_transaction(session_db=session_db,
                             user_profile_id=user.profile.id,
                             gold_before=gold_transaction['gold_before'],
                             gold_after=gold_transaction['gold_after'],
                             comment=f'Покупка книг опыта в магазине')

    await give_amulet_to_user(session_db=session_db,
                              owner_id=user.profile.id,
                              amulet=amulet)


async def buy_upgrade_item(session_db: AsyncSession,
                           upgrade_item_id: int,
                           user: User
                           ) -> None:
    """ Покупка книг в магазине предметов.
        Args:
            session_db: сессия базы данных
            upgrade_item_id: ID предмета усиления
            user: User + Profile
        Raises:
            UpgradeItemNotFoundError: если запрашивается покупка несуществующего предмета усиления
    """

    stmt_upgrade_item = select(UpgradeItemsType).where(UpgradeItemsType.id == upgrade_item_id)
    result = await session_db.execute(stmt_upgrade_item)
    upgrade_item = result.scalar_one_or_none()
    if upgrade_item is None:
        raise UpgradeItemNotFoundError()

    gold_transaction = await charge_user_gold(session_db=session_db,
                                              current_user=user,
                                              need_gold=upgrade_item.price)
    await create_transaction(session_db=session_db,
                             user_profile_id=user.profile.id,
                             gold_before=gold_transaction['gold_before'],
                             gold_after=gold_transaction['gold_after'],
                             comment=f'Покупка книг опыта в магазине')

    await add_upgrade_item_to_user(session_db=session_db,
                                   user_profile_id=user.profile.id,
                                   upgrade_item=upgrade_item)
