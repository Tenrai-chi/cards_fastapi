from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse
from urllib.parse import quote

from cards_app.auth.dependencies import get_current_user_with_profile
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.models.users import User
from cards_app.services.users import user_info_to_dto
from cards_app.use_cases.events import ViewNewsUseCase, ViewStartEventUseCase, GetAwardStartEventUseCase

router = APIRouter()

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get(path='/', name='home')
async def root(request: Request):
    url = request.url_for('news')
    return RedirectResponse(url=url, status_code=303)


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
    data: dict = await use_case.execute(page, size)

    context = {'request': request,
               'current_user': current_user_dto,
               'news': data.get('news_dto')
               }
    return templates.TemplateResponse(request=request,
                                      name='home/home_news.html',
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
    data: dict = await use_case.execute(current_user=current_user)
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
                                current_user: User | None = Depends(get_current_user_with_profile),
                                ):
    """ Получение награды стартового события """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = GetAwardStartEventUseCase(session_db)
    data: dict = await use_case.execute(current_user)
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
        return templates.TemplateResponse(request=request,
                                          name='errors/error_page.html',
                                          context={'error': data.get('error_message'),
                                                   'status_code': data.get('status_code'),
                                                   'current_user': current_user_dto},
                                          status_code=data.get('status_code')
                                          )
