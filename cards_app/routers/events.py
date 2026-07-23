from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse
from urllib.parse import quote

from cards_app.auth.dependencies import get_current_user_with_profile, get_current_user_id
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.models.users import User
from cards_app.services.users import user_info_to_dto
from cards_app.types import (ViewNewsUseCaseDict, ViewStartEventUseCaseDict, GetAwardStartEventUseCaseDict,
                             ViewUsersRatingDict)
from cards_app.use_cases.events import ViewNewsUseCase, ViewStartEventUseCase, GetAwardStartEventUseCase
from cards_app.use_cases.profile import ViewUsersRatingUseCase
from cards_app.routers.response_mapping import TEMPLATE_FOR_STATUS

router = APIRouter()

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get(path='/', name='home')
async def root(request: Request):
    url = request.url_for('news')
    return RedirectResponse(url=url, status_code=303)


@router.get(path='/error-{error_code}', name='view_error')
async def view_error(
        request: Request,
        current_user: User | None = Depends(get_current_user_with_profile),
        error_code: int = 500,
        error: str = None,
):
    """
    Просмотр страницы с ошибкой при редиректе.
    Обрабатываются ошибки 401, 403, 404 и 500.
    Если статус код не является одним из перечисленных, то по умолчанию выводит 500
    Args:
        request:
        current_user:
        error_code:
        error:

    Returns:

    """

    current_user_dto = await user_info_to_dto(current_user)
    context = {'request': request,
               'current_user': current_user_dto,
               'error': error,
               }

    template_name = TEMPLATE_FOR_STATUS.get(error_code, 'errors/error_500.html')
    status_code = error_code if error_code in TEMPLATE_FOR_STATUS else 500

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=context,
        status_code=status_code
    )


@router.get(path='/news', name='news')
async def view_news(request: Request,
                    session_db: AsyncSession = Depends(get_db_session),
                    current_user: User | None = Depends(get_current_user_with_profile),
                    page: int = 1,
                    size: int = 6
                    ):
    """ Просмотр новостей """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewNewsUseCase(session_db)
    data: ViewNewsUseCaseDict = await use_case.execute(page, size)

    context = {'request': request,
               'current_user': current_user_dto,
               'news': data.get('news_dto')
               }
    return templates.TemplateResponse(request=request,
                                      name='home/home_news.html',
                                      context=context,
                                      status_code=data.get('status_code'))


@router.get(path='/rating', name='rating')
async def view_rating(request: Request,
                      session_db: AsyncSession = Depends(get_db_session),
                      current_user: User | None = Depends(get_current_user_with_profile),
                      page: int = 1,
                      size: int = 25
                      ):
    """ Просмотр новостей """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewUsersRatingUseCase(session_db)
    data: ViewUsersRatingDict = await use_case.execute(page, size)

    context = {'request': request,
               'current_user': current_user_dto,
               'rating': data.get('rating_dto')
               }
    return templates.TemplateResponse(request=request,
                                      name='users/rating.html',
                                      context=context,
                                      status_code=data.get('status_code'))


@router.get(path='/start_event', name='start_event_page')
async def view_start_event(request: Request,
                           session_db: AsyncSession = Depends(get_db_session),
                           current_user: User | None = Depends(get_current_user_with_profile),
                           error: str = None,
                           success: str = None
                           ):
    """ Просмотр страницы стартового события """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewStartEventUseCase(session_db)
    data: ViewStartEventUseCaseDict = await use_case.execute(current_user=current_user)
    context = {'request': request,
               'current_user': current_user_dto,
               'awards': data.get('start_event_awards_dto'),
               'error_message': error,
               'success_message': success
               }
    return templates.TemplateResponse(request=request,
                                      name='home/home_start_event.html',
                                      context=context,
                                      status_code=data.get('status_code'))


@router.post(path='/start_event', name='get_award_start_event')
async def get_award_start_event(request: Request,
                                session_db: AsyncSession = Depends(get_db_session),
                                current_user_id: int | None = Depends(get_current_user_id),
                                ):
    """ Получение награды стартового события """

    use_case = GetAwardStartEventUseCase(session_db)
    data: GetAwardStartEventUseCaseDict = await use_case.execute(current_user_id=current_user_id)
    if data.get('new_card_id'):
        url = request.url_for('view_card', card_id=data.get('new_card_id'))
        return RedirectResponse(url, status_code=data.get('status_code'))

    elif data.get('status_code') == 303:
        success_msg = data['success_message']
        encoded_success = quote(success_msg)
        url = request.url_for('start_event_page')
        full_url = f'{url}?success={encoded_success}'
        return RedirectResponse(full_url, status_code=303)

    elif data.get('status_code') == 400:
        error_msg = data['error_message']
        encoded_error = quote(error_msg)
        url = request.url_for('start_event_page')
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)

    elif data.get('status_code') == 500:
        context = {'error': data.get('error_message'),
                   'status_code': data.get('status_code'),
                   'current_user': data.get('current_user_dto')}
        return templates.TemplateResponse(request=request,
                                          name='errors/error_page.html',
                                          context=context,
                                          status_code=data.get('status_code')
                                          )
