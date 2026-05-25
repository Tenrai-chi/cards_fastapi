import logging

from sqlalchemy.ext.asyncio import AsyncSession
from cards_app.models import User

logger = logging.getLogger(__name__)


async def update_guild_points_user(session_db: AsyncSession,
                                   user: User,
                                   result_battle: str
                                   ) -> None:
    """ Обновление очков гильдии пользователя после участия в рейтинговой битве.
        Args:
            session_db: сессия базы данных
            user: User + Profile + Guild пользователя
            result_battle: итог битвы
    """

    win_points = 30
    lose_points = 6
    draw_points = 15

    if not user.profile.guild:
        return

    if result_battle == 'win':
        user.profile.guild_point += win_points
        user.profile.guild.rating += win_points
    elif result_battle == 'lose':
        user.profile.guild_point += lose_points
        user.profile.guild.rating += lose_points
    elif result_battle == 'draw':
        user.profile.guild_point += draw_points
        user.profile.guild.rating += draw_points
    else:
        raise ValueError(f'Принят неверный результат битвы result_battle: {result_battle}')

    session_db.add(user)
    logger.info(f'Пользователь ID {user.id} получил и гильдия ID {user.profile.guild.id}'
                f' получили очки гильдии за битву')
