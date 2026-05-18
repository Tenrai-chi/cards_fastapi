import random
import logging
from datetime import datetime
from random import choice
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cards_app.config.exceptions import CardInStoreNotFoundError, CardNotOnSaleError, CardNotFoundError
from cards_app.models import Card, ClassCard, Rarity, Type, HistoryReceivingCards, AmuletItem, CardStore

logger = logging.getLogger(__name__)


async def get_card_with_details(session_db: AsyncSession,
                                card_id: int
                                ) -> Card:
    """ Возвращает карту с подгруженными амулетом, классом, типом и редкостью.
         Args:
            session_db: сессия базы данных
            card_id: ID карты, которую нужно получить.
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
            selectinload(Card.class_card),
            selectinload(Card.rarity_card),
            selectinload(Card.type_card),
            selectinload(Card.amulet).selectinload(AmuletItem.amulet_type)
        )
    )
    result_card = await session_db.execute(stmt_card)
    card = result_card.scalar_one_or_none()
    if card is None:
        logger.warning(f'Карта с id={card_id} не найдена в БД')
        raise CardNotFoundError(card_id)
    return card


async def get_rarities_and_classes(session_db: AsyncSession) -> dict:
    """ Получает из БД все классы карт и редкости для расчёта шанса выпадения
        и вывода полученной информации на страницу получения случайной карты
        Args:
            session_db: сессия базы данных

        Returns:
            dict:
                - rarities (list[Rarity]): список всех редкостей
                - classes (list[ClassCard]): список всех классов карт.
    """

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


async def generate_random_card(session_db: AsyncSession, owner_id: int) -> int:
    """ Генерирует случайную карту для указанного владельца.
        Args:
            session_db: сессия базы данных
            owner_id: ID профиля пользователя

        Returns:
            int: ID созданной карты
    """

    stmt_classes = select(ClassCard)
    result_classes = await session_db.execute(stmt_classes)
    class_card = choice(result_classes.scalars().all())

    stmt_types = select(Type)
    result_types = await session_db.execute(stmt_types)
    type_card = choice(result_types.scalars().all())

    stmt_rarities = select(Rarity)
    result_rarities = await session_db.execute(stmt_rarities)
    all_rarities = result_rarities.scalars().all()

    weights = [rarity.drop_chance for rarity in all_rarities]
    chosen_rarity = random.choices(all_rarities, weights=weights, k=1)[0]

    hp = random.randint(chosen_rarity.min_hp, chosen_rarity.max_hp)
    damage = random.randint(chosen_rarity.min_damage, chosen_rarity.max_damage)

    # Тут создание карты
    new_card = Card(owner_id=owner_id,
                    class_card_id=class_card.id,
                    type_id=type_card.id,
                    rarity_id=chosen_rarity.id,
                    level=1,
                    hp=hp,
                    damage=damage)

    session_db.add(new_card)
    await session_db.flush()
    logger.info(f'Сгенерирована случайная карта: id={new_card.id}, владелец={owner_id}')

    return new_card.id


async def generate_card_start_event(session_db: AsyncSession,
                                    user_id: int,
                                    rarity_name: str
                                    ) -> int:
    """ Создает случайную карту заданной редкости с максимальными характеристиками.
        Args:
            session_db: сессия базы данных
            user_id: ID профиля пользователя
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

    # Тут создание карты
    new_card = Card(owner_id=user_id,
                    class_card_id=class_card.id,
                    type_id=type_card.id,
                    rarity_id=rarity.id,
                    level=1,
                    hp=hp,
                    damage=damage)

    session_db.add(new_card)
    await session_db.flush()
    logger.info(f'Сгенерирована карта в стартовом событии: id={new_card.id}, владелец={user_id}')

    return new_card.id


async def create_new_card_from_template(session_db: AsyncSession,
                                        owner_id: int,
                                        card_temp: CardStore
                                        ) -> int:
    """ Создает новую карту пользователя по карте-шаблону из магазина.
       Args:
            session_db: сессия базы данных
            owner_id: ID профиля владельца карты
            card_temp: Объект CardStore — шаблон карты из магазина.
        Returns:
            int: ID созданной карты
    """

    new_card = Card(owner_id=owner_id,
                    class_card_id=card_temp.class_card_id,
                    type_id=card_temp.type_id,
                    rarity_id=card_temp.rarity_id,
                    level=1,
                    hp=card_temp.hp,
                    damage=card_temp.damage)

    session_db.add(new_card)
    await session_db.flush()
    logger.info(f'Создана карта: id={new_card.id}, владелец={owner_id}')

    return new_card.id


async def get_temp_card_in_store(session_db: AsyncSession, card_temp_id) -> CardStore:
    """ Получает карту из магазина по ее ID.
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
        logger.warning(f'Карта в магазине с id={card_temp_id} не найдена')
        raise CardInStoreNotFoundError(card_id=card_temp_id)

    if temp_card.sale_now is False:
        logger.warning(f'Карта в магазине с id={card_temp_id} на данный момент не продается')
        raise CardNotOnSaleError()

    return temp_card


async def get_all_cards_user(session_db: AsyncSession, owner_id: int) -> List[Card]:
    """ Возвращает список всех карт пользователя.
        Args:
            session_db: сессия базы данных
            owner_id: ID профиля владельца

        Returns:
            List[Card]: список карт, принадлежащих пользователю
    """

    stmt = select(Card).where(Card.owner_id == owner_id).order_by(Card.id)
    result = await session_db.execute(stmt)
    cards = list(result.scalars().all())
    return cards


async def create_record_in_history_receiving_card(session_db: AsyncSession,
                                                  card_id: int,
                                                  user_id: int,
                                                  method_receiving: str
                                                  ) -> None:
    """ Создает запись в таблице с историей получения карт.
        Args:
            session_db: сессия базы данных
            card_id: ID полученной карты
            user_id: ID профиля пользователя, получившего карту.
            method_receiving: Способ получения (покупка, генерация)
    """

    new_record = HistoryReceivingCards(card_id=card_id,
                                       date_and_time=datetime.now(),
                                       user_id=user_id,
                                       method_receiving=method_receiving)
    session_db.add(new_record)
    logger.info(f'Создана запись в истории получения карт: карта ID: {card_id} '
                f'получена пользователем ID {user_id} способом "{method_receiving}"')
