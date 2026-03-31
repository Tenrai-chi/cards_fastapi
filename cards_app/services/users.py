from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from cards_app.auth.dependencies import get_current_user_with_profile
from cards_app.models import User, Profile, Card, FightHistory, FavoriteUsers

from cards_app.config.security import decode_token
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings


async def get_profile_data(session_db: AsyncSession, user_id: int) -> User | None:
    """ Возвращает пользователя с профилем, гильдией, текущей картой и её амулетами """

    query = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.profile).selectinload(Profile.guild),
            selectinload(User.profile)
            .selectinload(Profile.current_card)
            .selectinload(Card.amulets)  # подгружаем амулеты текущей карты
        )
    )
    result = await session_db.execute(query)
    return result.scalar_one_or_none()


async def get_battle_stats(session_db: AsyncSession, profile1_id: int, profile2_id: int):
    """ Возвращает (победы profile1 над profile2, победы profile2 над profile1) """

    wins1 = await session_db.scalar(
        select(func.count())
        .where(FightHistory.winner_id == profile1_id, FightHistory.loser_id == profile2_id)
    )
    wins2 = await session_db.scalar(
        select(func.count())
        .where(FightHistory.winner_id == profile2_id, FightHistory.loser_id == profile1_id)
    )
    return wins1 or 0, wins2 or 0


async def get_fight_history(session_db: AsyncSession, profile_id: int, limit: int = 50):
    """ Возвращает список боёв, где профиль был участником, с подгрузкой соперника и карт """

    query = (
        select(FightHistory)
        .where((FightHistory.winner_id == profile_id) | (FightHistory.loser_id == profile_id))
        .order_by(desc(FightHistory.date_and_time))
        .limit(limit)
        .options(
            selectinload(FightHistory.winner).selectinload(Profile.user),  # подгружаем user для имени
            selectinload(FightHistory.loser).selectinload(Profile.user),
            selectinload(FightHistory.card_winner),
            selectinload(FightHistory.card_loser),
        )
    )
    result = await session_db.execute(query)
    return result.scalars().all()


async def is_favorite(db: AsyncSession, current_profile_id: int, target_profile_id: int) -> bool:
    query = select(FavoriteUsers).where(
        FavoriteUsers.user_id == current_profile_id,
        FavoriteUsers.favorite_user_id == target_profile_id
    )
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None

