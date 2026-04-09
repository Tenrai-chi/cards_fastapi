from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import quote

from cards_app.auth.dependencies import get_current_user_with_profile
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.services.users import user_info_to_dto
from cards_app.models.users import User
from cards_app.use_cases.profile import ViewProfileUseCase, AddFavoriteUserUseCase, RemoveFavoriteUserUseCase

router = APIRouter(prefix='/users', tags=['users'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get(path='/{user_id}', name='user_profile')
async def view_user_profile(request: Request,
                            user_id: int,
                            session_db: AsyncSession = Depends(get_db_session),
                            current_user: User | None = Depends(get_current_user_with_profile),
                            error: str = None,
                            success: str = None):
    """ Просмотр профиля пользователя """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewProfileUseCase(session_db)
    data: dict = await use_case.execute(current_user, user_id)
    if data.get('user_info'):
        context = {'request': request,
                   'current_user': current_user_dto,
                   'profile_dto': data['user_info'],
                   'error_message': error,
                   'success_message': success
                   }
        return templates.TemplateResponse(request=request,
                                          name='profile.html',
                                          context=context,
                                          status_code=data.get('status_code'))
    else:
        if data.get('status_code') in (404, 500):
            return templates.TemplateResponse(request=request,
                                              name='error_page.html',
                                              context={'error': data.get('error_message')},
                                              status_code=data.get('status_code')
                                              )


@router.post(path='/add_{user_id}', name='add_favorite_user')
async def add_user_favorite(request: Request,
                            user_id: int,
                            session_db: AsyncSession = Depends(get_db_session),
                            current_user: User | None = Depends(get_current_user_with_profile),
                            ):
    """ Добавление пользователя в список избранных.
        Редиректит на другие станицы в зависимости от успеха или неудачи.
    """

    use_case = AddFavoriteUserUseCase(session_db)
    data: dict = await use_case.execute(current_user=current_user,
                                        target_user_id=user_id)
    if data.get('success') is True:
        url = request.url_for('user_profile', user_id=user_id)
        full_url = f'{url}?error={data.get("success_message")}'
        return RedirectResponse(full_url, status_code=data.get('status_code'))
    else:
        error_msg = data.get('error_message')
        encoded_error = quote(error_msg)
        url = request.url_for('user_profile', user_id=user_id)
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=data.get('status_code'))


@router.post(path='/remove_{user_id}', name='remove_favorite_user')
async def remove_user_favorite(request: Request,
                               user_id: int,
                               session_db: AsyncSession = Depends(get_db_session),
                               current_user: User | None = Depends(get_current_user_with_profile),
                               ):
    """ Добавление пользователя в список избранных.
        Редиректит на другие станицы в зависимости от успеха или неудачи.
    """

    use_case = RemoveFavoriteUserUseCase(session_db)
    data: dict = await use_case.execute(current_user=current_user,
                                        target_user_id=user_id)
    if data.get('success') is True:
        url = request.url_for('user_profile', user_id=user_id)
        full_url = f'{url}?error={data.get("success_message")}'
        return RedirectResponse(full_url, status_code=data.get('status_code'))
    else:
        error_msg = data['error_message']
        encoded_error = quote(error_msg)
        url = request.url_for('user_profile', user_id=user_id)
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=data.get('status_code'))
