from typing import Optional
from datetime import datetime
from sqlalchemy import func, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from cards_app.models import User, Profile, FavoriteUsers, Card, FightHistory


async def get_base_info_profile(session: AsyncSession,
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
    result = await session.execute(stmt)
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
