from datetime import datetime
from typing import Optional
from sqlalchemy import func, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cards_app.config.exceptions import InsufficientFundsUserError, NotEnoughSlotsError
from cards_app.models import User, Profile, FavoriteUsers, Card, FightHistory, Transactions
from cards_app.services.cards import get_all_cards_user


async def get_base_info_profile(session_db: AsyncSession,
                                user_id: int
                                ) -> Optional[User]:
    """ Возвращает базовую информацию профиля с подгруженной гильдией """

    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.profile).selectinload(Profile.guild)
        )
    )
    result = await session_db.execute(stmt)
    return result.scalar_one_or_none()


async def get_battle_stats(session_db: AsyncSession, profile1_id: int, profile2_id: int):
    """ Возвращает статистику побед / поражений пользователя против другого """

    wins = await session_db.scalar(
        select(func.count())
        .where(FightHistory.winner_id == profile1_id, FightHistory.loser_id == profile2_id)
    )
    loses = await session_db.scalar(
        select(func.count())
        .where(FightHistory.winner_id == profile2_id, FightHistory.loser_id == profile1_id)
    )
    return wins or 0, loses or 0


async def get_fight_history_user(session_db: AsyncSession, profile_id: int, limit: int = 50):
    """ Возвращает список боёв, где профиль был участником, с подгрузкой соперника и карт """

    query = (
        select(FightHistory)
        .where((FightHistory.winner_id == profile_id) | (FightHistory.loser_id == profile_id))
        .order_by(desc(FightHistory.date_and_time))
        .limit(limit)
        .options(
            selectinload(FightHistory.winner).selectinload(Profile.user),
            selectinload(FightHistory.loser).selectinload(Profile.user),
            selectinload(FightHistory.card_winner).selectinload(Card.class_card),
            selectinload(FightHistory.card_winner).selectinload(Card.type_card),
            selectinload(FightHistory.card_loser).selectinload(Card.class_card),
            selectinload(FightHistory.card_loser).selectinload(Card.type_card),
        )
    )
    result = await session_db.execute(query)
    return result.scalars().all()


async def is_favorite(session_db: AsyncSession, current_profile_id: int, target_profile_id: int) -> bool:
    """ Возвращает флаг о том, находится ли выбранный пользователь в списке избранных у текущего """

    query = select(FavoriteUsers).where(
        FavoriteUsers.user_id == current_profile_id,
        FavoriteUsers.favorite_user_id == target_profile_id
    )
    result = await session_db.execute(query)
    return result.scalar_one_or_none() is not None


async def update_user_receiving_timer(session_db: AsyncSession, current_user: User):
    """ Обновление таймера при получении бесплатной карты """

    current_user.profile.receiving_timer = datetime.now()
    session_db.add(current_user.profile)


async def check_can_user_receive_card(session_db: AsyncSession, current_user: User, need_slots: int) -> None:
    """ Проверяет, хватит ли у пользователя места в инвентаре для новых карт.
        Если не хватает, то выбрасывает исключение
    """

    all_cards = await get_all_cards_user(session_db, current_user.profile.id)
    if need_slots > current_user.profile.card_slots - len(all_cards):
        raise NotEnoughSlotsError('У вас недостаточно места для новых карт')


async def charge_user_gold(session_db: AsyncSession, current_user: User, need_gold: int) -> dict:
    """ Списывает золото у пользователя.
        Если золота недостаточно поднимает ошибку
    """

    answer_data = {'gold_before': None,
                   'gold_after': None}

    if current_user.profile.gold < need_gold:
        raise InsufficientFundsUserError(current_user.profile.gold - need_gold)

    gold_after_buy = current_user.profile.gold - need_gold
    answer_data['gold_before'] = current_user.profile.gold
    answer_data['gold_after'] = gold_after_buy
    current_user.profile.gold = gold_after_buy

    session_db.add(current_user)

    return answer_data


async def create_transaction(session_db: AsyncSession,
                             user_id: int,
                             gold_before: int,
                             gold_after: int,
                             comment: str
                             ) -> None:
    """ Создает транзакцию пользователя """

    new_transaction = Transactions(date_and_time=datetime.now(),
                                   user_id=user_id,
                                   before=gold_before,
                                   after=gold_after,
                                   comment=comment)
    session_db.add(new_transaction)
