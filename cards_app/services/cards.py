import random
from datetime import datetime
from random import choice
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cards_app.config.exceptions import CardInStoreNotFoundError, CardNotOnSaleError, CardNotFoundError
from cards_app.models import Card, ClassCard, Rarity, Type, HistoryReceivingCards, AmuletItem, CardStore


async def get_card_with_details(session_db: AsyncSession,
                                card_id: int
                                ) -> Card:
    """ Возвращает карту с подгруженными амулетом, классом, типом и редкостью """

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
        raise CardNotFoundError(card_id)
    return card


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


async def generate_random_card(session_db: AsyncSession, owner_id: int) -> int:
    """ Генерация случайной карты """

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

    return new_card.id


async def create_new_card_from_template(session_db: AsyncSession,
                                        owner_id: int,
                                        card_temp: CardStore) -> int | None:
    """ Создает новую карту пользователя по карте-шаблону из магазина """

    new_card = Card(owner_id=owner_id,
                    class_card_id=card_temp.class_card_id,
                    type_id=card_temp.type_id,
                    rarity_id=card_temp.rarity_id,
                    level=1,
                    hp=card_temp.hp,
                    damage=card_temp.damage)

    session_db.add(new_card)
    await session_db.flush()

    return new_card.id


async def get_temp_card_in_store(session_db: AsyncSession, card_temp_id) -> CardStore:
    """ Получает карту из магазина.
        Если такой карты нет, то поднимает ошибку CardInStoreNotFoundError
        Если карта есть, но она не продается, то поднимает ошибку CardNotOnSaleError
    """

    stmt_temp_card = select(CardStore).where(CardStore.id == card_temp_id)
    result_temp_card = await session_db.execute(stmt_temp_card)
    temp_card = result_temp_card.scalars().one_or_none()

    if temp_card is None:
        raise CardInStoreNotFoundError(card_id=card_temp_id)

    if temp_card.sale_now is False:
        raise CardNotOnSaleError()

    return temp_card


async def get_all_cards_user(session_db: AsyncSession, owner_id: int) -> List[Card]:
    """ Возвращает все карты пользователя """

    stmt = select(Card).where(Card.owner_id == owner_id).order_by(Card.id)
    result = await session_db.execute(stmt)
    cards = list(result.scalars().all())
    return cards


async def create_record_in_history_receiving_card(session_db: AsyncSession,
                                                  card_id: int,
                                                  user_id: int,
                                                  method_receiving: str) -> None:
    """ Создает запись в таблице с историей получения карт """

    new_record = HistoryReceivingCards(card_id=card_id,
                                       date_and_time=datetime.now(),
                                       user_id=user_id,
                                       method_receiving=method_receiving)
    session_db.add(new_record)
