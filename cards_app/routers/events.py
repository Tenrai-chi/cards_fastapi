from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse, Response
from urllib.parse import quote

from cards_app.auth.dependencies import get_current_user_with_profile, get_current_user_id
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.models.users import User
from cards_app.routers.response_mapping import TEMPLATE_FOR_STATUS, get_error_template, RESPONSE_TYPE_TO_HTTP
from cards_app.schemas.response import (
    ViewNewsUseCaseResponse, ViewUsersRatingResponse, ViewStartEventUseCaseResponse,
    GetAwardStartEventUseCaseResponse
)
from cards_app.services.users import user_info_to_dto
from cards_app.use_cases.events import ViewUsersRatingUseCase, ViewNewsUseCase, ViewStartEventUseCase, GetAwardStartEventUseCase
from cards_app.utils.response_types import ResponseType


router = APIRouter()

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get(path='/', name='home')
async def root(request: Request) -> Response:
    """ Домашняя страница с перенаправлением на новости """

    url = request.url_for('news')
    return RedirectResponse(url=url, status_code=303)


@router.get(path='/error-{error_code}', name='view_error')
async def view_error(
        request: Request,
        current_user: User | None = Depends(get_current_user_with_profile),
        error_code: int = 500,
        error: str = None,
) -> Response:
    """
    Просмотр страницы с ошибкой.
    Обрабатываются ошибки 401, 403, 404 и 500.
    Если статус код не является одним из перечисленных, то по умолчанию выводит 500.
    Args:
        request: объект запроса FastAPI.
        current_user: текущий пользователь из зависимости.
        error_code: http статус ошибки, которую нужно показать.
        error: сообщение об ошибке, при наличии

    Returns:
        Response: рендеринг страницы с ошибкой, переданной другими роутерам.
    """

    current_user_dto = await user_info_to_dto(current_user)
    context = {
        'request': request,
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
async def view_news(
        request: Request,
        session_db: AsyncSession = Depends(get_db_session),
        current_user: User | None = Depends(get_current_user_with_profile),
        page: int = 1,
        size: int = 6
) -> Response:
    """
    Просмотр новостей.
    Args:
        request: объект запроса FastAPI.
        session_db: сессия базы данных из зависимости.
        current_user: текущий пользователь из зависимости.
        page: номер страницы.
        size: количество элементов на странице, по умолчанию 6.

    Returns:
        Response: рендеринг страницы с новостями.

    Notes:
        Возможные типы ответов:
        - SUCCESS: рендеринг данных.
        - SERVER_ERROR: рендеринг страницы ошибки.
    """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewNewsUseCase(session_db)
    data: ViewNewsUseCaseResponse = await use_case.execute(page, size)

    if data.response_type == ResponseType.SUCCESS:
        context = {'request': request,
                   'current_user': current_user_dto,
                   'news': data.news
                   }
        return templates.TemplateResponse(
            request=request,
            name='home/home_news.html',
            context=context,
            status_code=200
        )
    else:
        status_code = RESPONSE_TYPE_TO_HTTP.get(data.response_type, 500)
        template_name = get_error_template(status_code)
        context = {
            'error': data.error_message,
            'error_code': status_code,
            'current_user': current_user_dto
        }
        return templates.TemplateResponse(
            request=request,
            name=template_name,
            context=context,
            status_code=status_code
        )


@router.get(path='/rating', name='rating')
async def view_rating(
        request: Request,
        session_db: AsyncSession = Depends(get_db_session),
        current_user: User | None = Depends(get_current_user_with_profile),
        page: int = 1,
        size: int = 25
) -> Response:
    """
    Просмотр таблицы рейтинга.
    Args:
        request: объект запроса FastAPI.
        session_db: сессия базы данных из зависимости.
        current_user: текущий пользователь из зависимости.
        page: номер страницы.
        size: количество элементов на странице, по умолчанию 6.

    Returns:
        Response: рендеринг страницы при успехе или рендеринг страницы с ошибкой.

    Notes:
        Возможные типы ответов:
        - SUCCESS: рендеринг данных.
        - SERVER_ERROR: рендеринг страницы ошибки.
    """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewUsersRatingUseCase(session_db)
    data: ViewUsersRatingResponse = await use_case.execute(page, size)

    if data.response_type == ResponseType.SUCCESS:
        context = {
            'request': request,
            'current_user': current_user_dto,
            'rating': data.rating
        }
        return templates.TemplateResponse(
            request=request,
            name='users/rating.html',
            context=context,
            status_code=200
        )
    else:
        status_code = RESPONSE_TYPE_TO_HTTP.get(data.response_type, 500)
        template_name = get_error_template(status_code)
        context = {
            'error': data.error_message,
            'error_code': status_code,
            'current_user': current_user_dto
        }
        return templates.TemplateResponse(
            request=request,
            name=template_name,
            context=context,
            status_code=status_code
        )


@router.get(path='/start_event', name='start_event_page')
async def view_start_event(
        request: Request,
        session_db: AsyncSession = Depends(get_db_session),
        current_user: User | None = Depends(get_current_user_with_profile),
        error: str = None,
        success: str = None
) -> Response:
    """
    Просмотр страницы стартового события.
    Args:
        request: объект запроса FastAPI.
        session_db: сессия базы данных из зависимости.
        current_user: текущий пользователь из зависимости.
        error: сообщение об ошибке из query-параметра.
        success: сообщение об успехе из query-параметра.

    Returns:
        Response: рендеринг страницы при успехе или рендеринг страницы с ошибкой.

    Notes:
        Возможные типы ответов:
        - SUCCESS: рендеринг данных.
        - SERVER_ERROR: рендеринг страницы ошибки.
    """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewStartEventUseCase(session_db)
    data: ViewStartEventUseCaseResponse = await use_case.execute(current_user=current_user)
    if data.response_type == ResponseType.SUCCESS:
        context = {
            'request': request,
            'current_user': current_user_dto,
            'awards': data.start_event_awards,
            'error_message': error,
            'success_message': success
        }
        return templates.TemplateResponse(
            request=request,
            name='home/home_start_event.html',
            context=context,
            status_code=200
        )
    else:
        status_code = RESPONSE_TYPE_TO_HTTP.get(data.response_type, 500)
        template_name = get_error_template(status_code)
        context = {
            'error': data.error_message,
            'error_code': status_code,
            'current_user': current_user_dto
        }
        return templates.TemplateResponse(
            request=request,
            name=template_name,
            context=context,
            status_code=status_code
        )


@router.post(path='/start_event', name='get_award_start_event')
async def get_award_start_event(
        request: Request,
        session_db: AsyncSession = Depends(get_db_session),
        current_user_id: int | None = Depends(get_current_user_id),
) -> Response:
    """
    Получение награды стартового события.
    Args:
        request: объект запроса FastAPI.
        session_db: сессия базы данных из зависимости.
        current_user_id: ID текущего пользователя из зависимости.

    Returns:
        Response: редирект на страницу со стартовым событием, либо на просмотр новой карты,
        либо на страницу ошибки.

    Notes:
        Возможные типы ответов:
        - REDIRECT_WITH_INFO: редирект к обновленным данным.
        - REDIRECT_WITH_ERROR и UNAUTHORIZED: редирект на страницу получения карты с ошибкой.
        - UNAUTHORIZED и SERVER_ERROR редирект на страницу с ошибкой.
    """

    use_case = GetAwardStartEventUseCase(session_db)
    data: GetAwardStartEventUseCaseResponse = await use_case.execute(current_user_id=current_user_id)
    if data.response_type == ResponseType.REDIRECT_WITH_INFO:
        if data.new_card_id:
            success_msg = data.success_message
            encoded_success = quote(success_msg)
            url = request.url_for('view_card', card_id=data.new_card_id)
            full_url = f'{url}?success={encoded_success}'
            return RedirectResponse(full_url, status_code=303)
        else:
            success_msg = data.success_message
            encoded_success = quote(success_msg)
            url = request.url_for('start_event_page')
            full_url = f'{url}?success={encoded_success}'
            return RedirectResponse(full_url, status_code=303)

    elif data.response_type in (ResponseType.REDIRECT_WITH_ERROR, ResponseType.UNAUTHORIZED):
        error_msg = data.error_message
        encoded_success = quote(error_msg)
        url = request.url_for('start_event_page')
        full_url = f'{url}?error={encoded_success}'
        return RedirectResponse(full_url, status_code=303)

    else:
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        status_code = RESPONSE_TYPE_TO_HTTP.get(data.response_type, 500)
        url = request.url_for('view_error', error_code=status_code)
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)
