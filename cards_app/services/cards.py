import asyncio
import logging
import random

from datetime import datetime
from random import choice
from typing import List, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from cards_app.types import RaritiesAndClassesDict
from cards_app.exeptions import (
    CardInStoreNotFoundError, CardNotOnSaleError, CardNotFoundError, NotCardOwnerError,
    EmptyCardsForMergeError, TooManyCardsMergeError, SelfMergeError
)
from cards_app.models import Card, ClassCard, Rarity, Type, HistoryReceivingCards, AmuletItem, CardStore, Profile
from cards_app.utils.common import calculate_need_exp

logger = logging.getLogger(__name__)


async def get_card_with_details(
        session_db: AsyncSession,
        card_id: int,
        for_update: bool = False
) -> Card:
    """
    Возвращает карту с подгруженными амулетом, классом, типом и редкостью.
    Args:
        session_db: сессия базы данных
        card_id: ID карты, которую нужно получить
        for_update: флаг о том, что запрос на получение данных для изменения
    Returns:
        Card: Объект карты с подгруженными атрибутами:
            - class_card (ClassCard)
            - rarity_card (Rarity)
            - type_card (Type)
            - amulet (AmuletItem) с подгруженным amulet_type (AmuletType)
    Raises:
        CardNotFoundError: Если карта с указанным ID не найдена в БД.
    """

    stmt_card = (
        select(Card)
        .where(Card.id == card_id)
        .options(
            joinedload(Card.class_card),
            joinedload(Card.rarity_card),
            joinedload(Card.type_card),
            joinedload(Card.amulet).joinedload(AmuletItem.amulet_type),
        )
    )
    if for_update:
        stmt_card.with_for_update(of=Card)

    result_card = await session_db.execute(stmt_card)
    card = result_card.scalar_one_or_none()
    if card is None:
        logger.warning(f'Карта ID {card_id} не найдена')
        raise CardNotFoundError(card_id)
    return card


async def get_rarities_and_classes(session_db: AsyncSession) -> RaritiesAndClassesDict:
    """
    Получает из БД все классы карт и редкости для расчёта шанса выпадения
    и вывода полученной информации на страницу получения случайной карты
    Args:
        session_db: сессия базы данных
    Returns:
        dict RaritiesAndClassesDict:
            - rarities (list[Rarity]): список всех редкостей
            - classes (list[ClassCard]): список всех классов
"""

    answer_data: RaritiesAndClassesDict = {
        'rarities': None,
        'classes': None
    }
    result_classes = await session_db.execute(select(ClassCard))
    all_classes = list(result_classes.scalars().all())
    answer_data['classes'] = all_classes

    result_rarities = await session_db.execute(select(Rarity))
    all_rarities = list(result_rarities.scalars().all())
    answer_data['rarities'] = all_rarities

    return answer_data


async def generate_random_card(session_db: AsyncSession, owner_id: int) -> int:
    """
    Генерирует случайную карту для указанного владельца.
    Args:
        session_db: сессия базы данных
        owner_id: ID Profile пользователя

    Returns:
        int: ID созданной карты
    """

    result_classes = await session_db.execute(select(ClassCard))
    class_card = choice(result_classes.scalars().all())

    result_types = await session_db.execute(select(Type))
    type_card = choice(result_types.scalars().all())

    result_rarities = await session_db.execute(select(Rarity))
    all_rarities = result_rarities.scalars().all()

    weights = [rarity.drop_chance for rarity in all_rarities]
    chosen_rarity = random.choices(all_rarities, weights=weights, k=1)[0]

    hp = random.randint(chosen_rarity.min_hp, chosen_rarity.max_hp)
    damage = random.randint(chosen_rarity.min_damage, chosen_rarity.max_damage)

    # Создание карты
    new_card = Card(
        owner_id=owner_id,
        class_card_id=class_card.id,
        type_id=type_card.id,
        rarity_id=chosen_rarity.id,
        level=1,
        hp=hp,
        damage=damage
    )

    session_db.add(new_card)
    await session_db.flush()
    logger.info(f'Сгенерирована случайная карта: id={new_card.id}, владелец={owner_id}')

    return new_card.id


async def generate_card_start_event(
        session_db: AsyncSession,
        user_profile_id: int,
        rarity_name: str
) -> int:
    """
    Создает случайную карту заданной редкости с максимальными характеристиками.
    Args:
        session_db: сессия базы данных
        user_profile_id: ID Profile пользователя
        rarity_name: название редкости карты для получения ее ID
    Returns:
        int: ID созданной карты
    """

    stmt_classes = select(ClassCard)
    result_classes = await session_db.execute(stmt_classes)
    class_card = choice(result_classes.scalars().all())

    stmt_types = select(Type)
    result_types = await session_db.execute(stmt_types)
    type_card = choice(result_types.scalars().all())

    stmt_rarity = select(Rarity).where(Rarity.name == rarity_name)
    result_rarity = await session_db.execute(stmt_rarity)
    rarity = result_rarity.scalar_one_or_none()

    hp = rarity.max_hp
    damage = rarity.max_damage

    new_card = Card(
        owner_id=user_profile_id,
        class_card_id=class_card.id,
        type_id=type_card.id,
        rarity_id=rarity.id,
        level=1,
        hp=hp,
        damage=damage
    )

    session_db.add(new_card)
    await session_db.flush()
    logger.info(f'Сгенерирована карта в стартовом событии: ID {new_card.id}, владелец ID {user_profile_id}')

    return new_card.id


async def create_new_card_from_template(
        session_db: AsyncSession,
        owner_id: int,
        card_temp: CardStore
) -> int:
    """
    Создает новую карту пользователя по карте-шаблону из магазина при покупке.
    Args:
        session_db: сессия базы данных
        owner_id: ID Profile владельца карты
        card_temp: Объект CardStore — шаблон карты из магазина.
    Returns:
        int: ID созданной карты
    """

    new_card = Card(
        owner_id=owner_id,
        class_card_id=card_temp.class_card_id,
        type_id=card_temp.type_id,
        rarity_id=card_temp.rarity_id,
        level=1,
        hp=card_temp.hp,
        damage=card_temp.damage
    )

    session_db.add(new_card)
    await session_db.flush()
    logger.info(f'Создана карта: ID {new_card.id}, владелец ID {owner_id}')

    return new_card.id


async def get_temp_card_in_store(session_db: AsyncSession, card_temp_id: int) -> CardStore:
    """
    Получает карту из магазина по ее ID.
    Args:
        session_db: сессия базы данных
        card_temp_id: ID карты в магазине
    Returns:
        CardStore: объект карты-шаблона, доступной для покупки
    Raises:
        CardInStoreNotFoundError: если карта с указанным ID не найдена в магазине.
        CardNotOnSaleError: если карта найдена, но поле sale_now == False (не продаётся в данный момент).
    """

    stmt_temp_card = select(CardStore).where(CardStore.id == card_temp_id)
    result_temp_card = await session_db.execute(stmt_temp_card)
    temp_card = result_temp_card.scalars().one_or_none()

    if temp_card is None:
        logger.warning(f'Карта в магазине ID {card_temp_id} не найдена')
        raise CardInStoreNotFoundError(card_id=card_temp_id)

    if temp_card.sale_now is False:
        logger.warning(f'Карта в магазине ID {card_temp_id} на данный момент не продается')
        raise CardNotOnSaleError()

    return temp_card


async def get_all_cards_user(
        session_db: AsyncSession,
        owner_id: int,
        with_details: bool = False
) -> List[Card]:
    """
    Возвращает список всех карт пользователя.
    Args:
        session_db: сессия базы данных
        owner_id: ID Profile владельца
        with_details: маркер нужно ли подгружать детали
    Returns:
        List[Card]: список карт, принадлежащих пользователю
    """

    stmt_user_cards = select(Card).where(Card.owner_id == owner_id)

    if with_details:
        stmt_user_cards = (
            stmt_user_cards
            .join(Card.rarity_card)
            .options(
                selectinload(Card.class_card),
                selectinload(Card.type_card),
                selectinload(Card.rarity_card)
            )
            .order_by(Card.level.desc(), Rarity.id, Card.id)
        )

    result = await session_db.execute(stmt_user_cards)
    cards = list(result.scalars().all())
    return cards


async def create_record_in_history_receiving_card(
        session_db: AsyncSession,
        card_id: int,
        user_profile_id: int,
        method_receiving: str
) -> None:
    """
    Создает запись в таблице с историей получения карт.
    Args:
        session_db: сессия базы данных
        card_id: ID полученной карты
        user_profile_id: ID Profile пользователя, получившего карту.
        method_receiving: Способ получения (покупка, генерация)
    """

    new_record = HistoryReceivingCards(
        card_id=card_id,
        date_and_time=datetime.now(),
        user_id=user_profile_id,
        method_receiving=method_receiving
    )
    session_db.add(new_record)
    logger.info(f'Создана запись в истории получения карт: карта ID: {card_id} '
                f'получена пользователем ID {user_profile_id} способом "{method_receiving}"')


async def update_card_experience(
        session_db: AsyncSession,
        card: Card
) -> None:
    """
    Получение опыта карты в битве.
    Args:
        session_db: сессия базы данных
        card: карта
    """

    add_exp = 75

    if card.level == card.rarity_card.max_level:
        return

    card.experience_bar += add_exp

    need_exp_for_level = calculate_need_exp(level=card.level)
    if card.experience_bar >= need_exp_for_level:
        card.experience_bar -= need_exp_for_level
        card.level += 1

        # Если достигнут максимальный уровень, прогресс опыта обнуляется
        if card.level == card.rarity_card.max_level:
            card.experience_bar = 0

        # Увеличение характеристик карты
        await increase_stats(session_db=session_db, card=card)
    session_db.add(card)
    logger.info(f'Обновлен опыт карты ID {card.id}')


async def increase_stats(
        session_db: AsyncSession,
        card: Card,
        new_level: int = 1
) -> None:
    """
    Увеличение характеристик карты при получении уровня.
    Args:
        session_db: сессия базы данных
        card: карта
        new_level: новый уровень
    """

    card.damage += card.rarity_card.coefficient_damage_for_level * new_level
    card.hp += card.rarity_card.coefficient_hp_for_level * new_level
    session_db.add(card)

    logger.info(f'Карта ID {card.id} изменила свои характеристики при получении уровня')


async def get_cards_in_trading(session_db: AsyncSession) -> list[Card]:
    """
    Возвращает список карт, которые продают пользователи.
    Args:
        session_db: сессия базы данных
    Returns:
        list[Card]: карты в продаже
    """

    stmt_cards = (
        select(Card)
        .join(Card.rarity_card)
        .where(Card.sale_status == True)
        .options(
            joinedload(Card.class_card),
            joinedload(Card.type_card),
            joinedload(Card.rarity_card),
            joinedload(Card.owner).joinedload(Profile.user)
        )
        .order_by(Card.rarity_id, Card.id)
    )

    result = await session_db.execute(stmt_cards)
    cards = list(result.scalars().all())
    return cards


async def get_cards_for_merge(
        session_db: AsyncSession,
        current_card_id: int,
        owner_id: int
) -> tuple[Card, list[Card]]:
    """
    Возвращает список карт, подходящих для слияния.
    Args:
        session_db: сессия базы данных
        current_card_id: ID карты для слияния
        owner_id: ID Profile текущего пользователя
    Returns:
        tuple:
            - current_card (Card):
            - cards_for_merge (list[Card]):
    Rises:
        NotCardOwnerError: если пользователь не является владельцем карты
        CardNotFoundError: если карта не найдена в базе данных
    """

    stmt_current_card = (
        select(Card)
        .where(Card.id == current_card_id)
        .options(
            selectinload(Card.class_card),
            selectinload(Card.type_card),
            selectinload(Card.rarity_card),
        )
    )
    result = await session_db.execute(stmt_current_card)
    current_card = result.scalar_one_or_none()
    if current_card is None:
        raise CardNotFoundError(card_id=current_card_id)
    if current_card.owner_id != owner_id:
        raise NotCardOwnerError()

    stmt_cards_for_merge = (
        select(Card)
        .where(
            Card.owner_id == owner_id,
            Card.class_card_id == current_card.class_card_id,
            Card.type_id == current_card.type_id,
            Card.rarity_id == current_card.rarity_id,
            Card.id != current_card.id
        )
        .options(
            selectinload(Card.class_card),
            selectinload(Card.type_card),
            selectinload(Card.rarity_card),
        )
    )

    result = await session_db.execute(stmt_cards_for_merge)
    cards_for_merge = list(result.scalars().all())

    return current_card, cards_for_merge


async def increase_merger(
        session_db: AsyncSession,
        card: Card,
        add_merge: int
) -> None:
    """
    Повышает уровень слияния карты на add_merge
    Args:
        session_db: сессия базы данных
        card: текущая карта
        add_merge: количество полученных уровней слияния
        """

    card.merger += add_merge
    session_db.add(card)
    logger.info(f'Карта ID {card.id} повысила уровень слияния на {add_merge}')


async def merge_card(
        session_db: AsyncSession,
        current_card_id: int,
        cards_for_merge_ids: list[int],
        owner_id: int
) -> None:
    """
    Процесс слияния карт.
    Получает текущую карту и карты для слияния и блокирует их.
    Проверяет, что пользователь является владельцем всех карт и они существуют.
    Запускает увеличение уровня слияния текущей карты
    и параллельное удаление карт для слияния
    Args:
        session_db: сессия базы данных
        current_card_id: ID текущей карты для повышения уровня слияния
        cards_for_merge_ids: список ID карт, которые будут уничтожены для повышения
        owner_id: ID Profile пользователя, запросившего слияние
    Raises:
        CardNotFoundError: если карта(ы) не были найдены в базе данных
        NotCardOwnerError: если пользователь не является владельцем карт(ы)
        TooManyCardsMergeError: список карт для пожертвования больше чем требуется
        SelfMergeError: если пользователь пытается пожертвовать текущую карту
    """

    if current_card_id in cards_for_merge_ids:
        logger.warning(f'Попытка пользователя ID Profile {owner_id} '
                       f'слить в карту ID {current_card_id} саму себя')
        raise SelfMergeError

    stmt_current_card = (
        select(Card)
        .where(Card.id == current_card_id)
        .with_for_update()
    )
    result_card = await session_db.execute(stmt_current_card)
    current_card = result_card.scalar_one_or_none()

    if current_card is None:
        logger.warning(f'Пользователь ID {owner_id} попытался увеличить уровень слияния карты ID {current_card_id}, '
                       f'но она не существует')
        raise CardNotFoundError(card_id=current_card_id)

    if current_card.owner_id != owner_id:
        logger.warning(f'ID Pofile {owner_id} не является владельцем карты ID {current_card_id} '
                       f'и не может повысить ее уровень слияния')
        raise NotCardOwnerError

    if not cards_for_merge_ids:
        logger.warning(
            f'Пользователь ID Profile {owner_id} попытался увеличить уровень слияния карты ID {current_card_id} '
            f'без подходящих для этого карт')
        raise EmptyCardsForMergeError

    if current_card.max_merger - current_card.merger < len(cards_for_merge_ids):
        logger.warning(
            f'Пользователь ID Profile{owner_id} попытался увеличить уровень слияния карты ID {current_card_id} '
            f'но было выбрано больше карт, чем необходимо')
        raise TooManyCardsMergeError

    stmt_cards_for_merge = (
        select(Card)
        .where(Card.id.in_(cards_for_merge_ids))
        .with_for_update()
    )
    result_cards_for_merge = await session_db.execute(stmt_cards_for_merge)
    cards_for_merge = result_cards_for_merge.scalars().all()

    for card_for_merge in cards_for_merge:
        if card_for_merge.owner_id != owner_id:
            logger.warning(
                f'Пользователь ID Profile {owner_id} не является владельцем карты, которую выбрал для слияния')
            raise NotCardOwnerError

    if len(cards_for_merge_ids) != len(cards_for_merge):
        logger.warning(f'Пользователь ID {owner_id} попытался слить карту, не являясь ее владельцем')
        raise CardNotFoundError()

    # Параллельное удаление карт
    update_tasks = [clear_owner_card(session_db, card) for card in cards_for_merge]
    await asyncio.gather(*update_tasks)

    await increase_merger(
        session_db=session_db,
        card=current_card,
        add_merge=len(cards_for_merge)
    )


async def clear_owner_card(
        session_db: AsyncSession,
        card: Card,
) -> None:
    """
    Обнуляет владельца у карты
    Args:
    session_db: сессия базы данных
    card: карты, у которой необходимо удалить владельца
    """

    card.owner_id = None
    session_db.add(card)
    logger.info(f'У карты {card.id} удалён владелец')


async def generate_max_stat_ur_card(
        session_db: AsyncSession,
        user_profile_id: int,
) -> int:
    """
    Создает UR карту с максимальным значением здоровья или урона.
    Используется при открытии сундука с UR картой
    Args:
        session_db: сессия базы данных
        user_profile_id: ID Profile пользователя
    Returns:
        int: ID созданной карты
    """

    stmt_classes = select(ClassCard)
    result_classes = await session_db.execute(stmt_classes)
    class_card = choice(result_classes.scalars().all())

    stmt_types = select(Type)
    result_types = await session_db.execute(stmt_types)
    type_card = choice(result_types.scalars().all())

    stmt_rarity = select(Rarity).where(Rarity.name == 'UR')
    result_rarity = await session_db.execute(stmt_rarity)
    rarity = result_rarity.scalar_one_or_none()

    if random.choice(['hp', 'damage']) == 'hp':
        hp = rarity.max_hp
        damage = random.randint(cast(int, rarity.min_hp), cast(int, rarity.max_hp))
    else:
        hp = random.randint(cast(int, rarity.min_damage), cast(int, rarity.max_damage))
        damage = rarity.max_damage

    new_card = Card(
        owner_id=user_profile_id,
        class_card_id=class_card.id,
        type_id=type_card.id,
        rarity_id=rarity.id,
        level=1,
        hp=hp,
        damage=damage
    )

    session_db.add(new_card)
    await session_db.flush()
    logger.info(f'Сгенерирована карта при покупке сундука: id={new_card.id},'
                f' владелец={user_profile_id}')

    return new_card.id
