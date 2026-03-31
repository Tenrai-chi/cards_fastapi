from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession
from cards_app.auth.dependencies import get_current_user_with_profile
from cards_app.models import User
from cards_app.services.users import (get_profile_data, get_battle_stats, get_fight_history,
                                      is_favorite)

from cards_app.config.security import decode_token
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings

router = APIRouter(prefix='/users', tags=['users'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get('/{user_id}')
async def user_profile(request: Request,
                       user_id: int,
                       session_db: AsyncSession = Depends(get_db_session),
                       current_user: User | None = Depends(get_current_user_with_profile)):
    """ Просмотр профиля пользователя.
        Для гостей и хозяина профиля разные данные.
        Для не авторизованных пользователей информации минимум.

        Базовое: Профиль, гильдия, избранная карта, победы/поражения, амулет избранной карты (если есть)
        Гость: Победы/поражения против.
        Хозяин: Почта из user (и так есть), история боев
    """

    # Неавторизованный пользователь (базовый набор)
    base_user_info = await get_profile_data(session_db, user_id)
    if not base_user_info:
        return templates.TemplateResponse(
            request=request,
            name='404.html',
            context={'request': request, 'error': 'Пользователь не найден'},
            status_code=404
        )

    # Базовый контекст
    context = {
        'request': request,
        'user_info': base_user_info,
        'current_user': current_user,
        'user': current_user
    }

    # Хозяин
    profile_id = base_user_info.profile.id
    if current_user and current_user.id == user_id:
        context['fight_history'] = await get_fight_history(session_db, profile_id)

    # Гость
    elif current_user:
        current_profile_id = current_user.profile.id
        wins, losses = await get_battle_stats(session_db, current_profile_id, profile_id)
        context['wins_vs_users'] = wins
        context['losses_vs_users'] = losses
        context['is_favorite'] = await is_favorite(session_db, current_profile_id, profile_id)

    return templates.TemplateResponse(request=request,
                                      name='profile.html',
                                      context=context)
