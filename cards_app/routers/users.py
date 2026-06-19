from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import quote

from cards_app.auth.dependencies import get_current_user_with_profile, get_current_user_id
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.services.users import user_info_to_dto
from cards_app.models.users import User
from cards_app.types import (ViewProfileUseCaseDict, AddFavoriteUserUseCaseDict, RemoveFavoriteUserUseCaseDict,
                             FavoriteUsersUseCaseDict, UserTransactionsUseCaseDict)
from cards_app.use_cases.figth import ProcessFightUseCase
from cards_app.use_cases.profile import (ViewProfileUseCase, AddFavoriteUserUseCase, RemoveFavoriteUserUseCase,
                                         FavoriteUsersUseCase, UserTransactionsUseCase)

router = APIRouter(prefix='/users', tags=['users'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get(path='/favorite_users', name='favorite_users')
async def view_favorite_users(request: Request,
                              session_db: AsyncSession = Depends(get_db_session),
                              current_user: User | None = Depends(get_current_user_with_profile),
                              ):

    current_user_dto = await user_info_to_dto(current_user)
    use_case = FavoriteUsersUseCase(session_db)
    data: FavoriteUsersUseCaseDict = await use_case.execute(current_user=current_user)

    if data.get('favorite_users_dto'):
        context = {'request': request,
                   'current_user': current_user_dto,
                   'favorite_users_dto': data.get('favorite_users_dto'),
                   }

        return templates.TemplateResponse(request=request,
                                          name='users/favorite_users.html',
                                          context=context,
                                          status_code=data.get('status_code'))
    else:
        if data.get('status_code') == 404:
            return templates.TemplateResponse(request=request,
                                              name='errors/error_page.html',
                                              context={'error': data.get('error_message'),
                                                       'status_code': data.get('status_code'),
                                                       'current_user': current_user_dto},
                                              status_code=data.get('status_code')
                                              )


@router.get(path='/transactions', name='transactions')
async def transactions(request: Request,
                       session_db: AsyncSession = Depends(get_db_session),
                       current_user: User | None = Depends(get_current_user_with_profile),
                       ):
    """ Просмотр транзакций пользователя """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = UserTransactionsUseCase(session_db)
    data: UserTransactionsUseCaseDict = await use_case.execute(current_user=current_user)
    if data.get('transactions_dto'):
        context = {'request': request,
                   'current_user': current_user_dto,
                   'transactions_dto': data['transactions_dto'],
                   }

        return templates.TemplateResponse(request=request,
                                          name='users/transactions.html',
                                          context=context,
                                          status_code=data.get('status_code'))
    else:
        if data.get('status_code') == 400:
            return templates.TemplateResponse(request=request,
                                              name='errors/error_page.html',
                                              context={'error': data.get('error_message'),
                                                       'status_code': data.get('status_code'),
                                                       'current_user': current_user_dto},
                                              status_code=data.get('status_code')
                                              )


@router.get(path='/{user_id}', name='user_profile')
async def view_user_profile(request: Request,
                            user_id: int,
                            session_db: AsyncSession = Depends(get_db_session),
                            current_user: User | None = Depends(get_current_user_with_profile),
                            error: str = None,
                            success: str = None
                            ):
    """ Просмотр профиля пользователя.
        Принимает редиректы с сообщениями об успехе или ошибке.
    """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewProfileUseCase(session_db)
    data: ViewProfileUseCaseDict = await use_case.execute(current_user, user_id)
    if data.get('user_info'):
        context = {'request': request,
                   'current_user': current_user_dto,
                   'profile_dto': data['user_info'],
                   'error_message': error,
                   'success_message': success
                   }

        return templates.TemplateResponse(request=request,
                                          name='users/profile.html',
                                          context=context,
                                          status_code=data.get('status_code'))
    else:
        if data.get('status_code') in (404, 500):
            return templates.TemplateResponse(request=request,
                                              name='errors/error_page.html',
                                              context={'error': data.get('error_message'),
                                                       'status_code': data.get('status_code'),
                                                       'current_user': current_user_dto},
                                              status_code=data.get('status_code')
                                              )


@router.post(path='/add_{user_id}', name='add_favorite_user')
async def add_user_favorite(request: Request,
                            user_id: int,
                            session_db: AsyncSession = Depends(get_db_session),
                            current_user_id: int | None = Depends(get_current_user_id),
                            ):
    """ Добавление пользователя в список избранных """

    use_case = AddFavoriteUserUseCase(session_db)
    data: AddFavoriteUserUseCaseDict = await use_case.execute(current_user_id=current_user_id,
                                                              target_user_id=user_id)
    if data.get('success') is True:
        url = request.url_for('user_profile', user_id=user_id)
        full_url = f'{url}?success={data.get("success_message")}'
        return RedirectResponse(full_url, status_code=data.get('status_code'))
    else:
        if data.get('status_code') in (404, 500):
            return templates.TemplateResponse(request=request,
                                              name='errors/error_page.html',
                                              context={'error': data.get('error_message'),
                                                       'status_code': data.get('status_code'),
                                                       'current_user': data.get('current_user_dto')},
                                              status_code=data.get('status_code')
                                              )
        else:
            error_msg = data.get('error_message')
            encoded_error = quote(error_msg)
            url = request.url_for('user_profile', user_id=user_id)
            full_url = f'{url}?error={encoded_error}'
            return RedirectResponse(full_url, status_code=303)


@router.post(path='/remove_{user_id}', name='remove_favorite_user')
async def remove_user_favorite(request: Request,
                               user_id: int,
                               session_db: AsyncSession = Depends(get_db_session),
                               current_user_id: int | None = Depends(get_current_user_id),
                               ):
    """ Добавление пользователя в список избранных """

    use_case = RemoveFavoriteUserUseCase(session_db)
    data: RemoveFavoriteUserUseCaseDict = await use_case.execute(current_user_id=current_user_id,
                                                                 target_user_id=user_id)

    if data.get('success') is True:
        url = request.url_for('user_profile', user_id=user_id)
        full_url = f'{url}?success={data.get("success_message")}'
        return RedirectResponse(full_url, status_code=data.get('status_code'))
    else:
        if data.get('status_code') in (404, 500):
            context = {'error': data.get('error_message'),
                       'status_code': data.get('status_code'),
                       'current_user': data.get('current_user_dto')}
            return templates.TemplateResponse(request=request,
                                              name='errors/error_page.html',
                                              context=context,
                                              status_code=data.get('status_code')
                                              )
        else:
            error_msg = data.get('error_message')
            encoded_error = quote(error_msg)
            url = request.url_for('user_profile', user_id=user_id)
            full_url = f'{url}?error={encoded_error}'
            return RedirectResponse(full_url, status_code=303)


@router.post(path='/fight_{user_id}', name='fight_user')
async def fight_user(request: Request,
                     user_id: int,
                     session_db: AsyncSession = Depends(get_db_session),
                     current_user: User | None = Depends(get_current_user_with_profile),
                     ):
    """ Рейтинговый бой между участниками """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ProcessFightUseCase(session_db)
    data: dict = await use_case.execute(user=current_user,
                                        enemy_id=user_id)
    if data.get('fight_dto'):
        context = {'request': request,
                   'current_user': current_user_dto,
                   'fight_dto': data.get('fight_dto'),
                   }

        return templates.TemplateResponse(request=request,
                                          name='fights/rating_fight.html',
                                          context=context,
                                          status_code=data.get('status_code'))
    else:
        if data.get('status_code') == 500:
            return templates.TemplateResponse(request=request,
                                              name='errors/error_page.html',
                                              context={'error': data.get('error_message'),
                                                       'status_code': data.get('status_code'),
                                                       'current_user': current_user_dto},
                                              status_code=data.get('status_code')
                                              )
        else:
            error_msg = data.get('error_message')
            encoded_error = quote(error_msg)
            url = request.url_for('user_profile', user_id=user_id)
            full_url = f'{url}?error={encoded_error}'
            return RedirectResponse(full_url, status_code=303)
