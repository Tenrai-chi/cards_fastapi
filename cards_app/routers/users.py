from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import quote

from cards_app.auth.dependencies import get_current_user_with_profile, get_current_user_id
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.routers.response_mapping import RESPONSE_TYPE_TO_HTTP, get_error_template
from cards_app.schemas.response import (
    FavoriteUsersUseCaseResponse, UserTransactionsUseCaseResponse,
    ViewProfileUseCaseResponse, ToggleFavoriteUserUseCaseResponse, ProcessFightUseCaseResponse
)
from cards_app.services.users import user_info_to_dto
from cards_app.models.users import User

from cards_app.use_cases.figth import ProcessFightUseCase
from cards_app.use_cases.profile import (
    ViewProfileUseCase, AddFavoriteUserUseCase, RemoveFavoriteUserUseCase,
    FavoriteUsersUseCase, UserTransactionsUseCase
)
from cards_app.utils.response_types import ResponseType

router = APIRouter(prefix='/users', tags=['users'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get(path='/favorite_users', name='favorite_users')
async def view_favorite_users(
        request: Request,
        session_db: AsyncSession = Depends(get_db_session),
        current_user: User | None = Depends(get_current_user_with_profile),
) -> Response:
    """
    Просмотр списка избранных пользователей.
    Args:
        request: объект запроса FastAPI.
        session_db: сессия базы данных из зависимости.
        current_user: текущий пользователь из зависимости.

    Returns:
        Response: рендеринг страницы с списком избранных, или ошибкой.
    Notes:
        Возможные типы ответов:
        - SUCCESS: рендеринг данных.
        - UNAUTHORIZED и SERVER_ERROR: рендеринг страницы с ошибкой.
    """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = FavoriteUsersUseCase(session_db)
    data: FavoriteUsersUseCaseResponse = await use_case.execute(current_user=current_user)

    if data.response_type == ResponseType.SUCCESS:
        context = {
            'request': request,
            'current_user': current_user_dto,
            'favorite_users_dto': data.favorite_users,
        }

        return templates.TemplateResponse(
            request=request,
            name='users/favorite_users.html',
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


@router.get(path='/transactions', name='transactions')
async def transactions(
        request: Request,
        session_db: AsyncSession = Depends(get_db_session),
        current_user: User | None = Depends(get_current_user_with_profile),
) -> Response:
    """
    Просмотр транзакций пользователя.
    Args:
        request: объект запроса FastAPI.
        session_db: сессия базы данных из зависимости.
        current_user: текущий пользователь из зависимости.

    Returns:
        Response: рендеринг страницы транзакциями.
    Notes:
        Возможные типы ответов:
        - SUCCESS: рендеринг данных.
        - UNAUTHORIZED, SERVER_ERROR: рендеринг страницы с ошибкой.
    """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = UserTransactionsUseCase(session_db)
    data: UserTransactionsUseCaseResponse = await use_case.execute(current_user=current_user)
    if data.response_type == ResponseType.SUCCESS:
        context = {
            'request': request,
            'current_user': current_user_dto,
            'transactions_dto': data.transactions,
        }

        return templates.TemplateResponse(
            request=request,
            name='users/transactions.html',
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


@router.get(path='/{user_id}', name='user_profile')
async def view_user_profile(
        request: Request,
        user_id: int,
        session_db: AsyncSession = Depends(get_db_session),
        current_user: User | None = Depends(get_current_user_with_profile),
        error: str = None,
        success: str = None
) -> Response:
    """
    Просмотр профиля пользователя.
    Args:
        request: объект запроса FastAPI.
        user_id: ID целевого пользователя.
        session_db: сессия базы данных из зависимости.
        current_user: текущий пользователь из зависимости.
        error: сообщение об ошибке из query-параметра.
        success: сообщение о успехе из query-параметра.

    Returns:
        Response: рендеринг страницы с получением бесплатной карты.
    Notes:
        Возможные типы ответов:
        - SUCCESS: рендеринг данных.
        - NOT_FOUND и SERVER_ERROR: рендеринг страницы с ошибкой.
    """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewProfileUseCase(session_db)
    data: ViewProfileUseCaseResponse = await use_case.execute(current_user, user_id)
    if data.response_type == ResponseType.SUCCESS:
        context = {
            'request': request,
            'current_user': current_user_dto,
            'profile_dto': data.user_info,
            'error_message': error,
            'success_message': success
        }

        return templates.TemplateResponse(
            request=request,
            name='users/profile.html',
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


@router.post(path='/add_{user_id}', name='add_favorite_user')
async def add_user_favorite(
        request: Request,
        user_id: int,
        session_db: AsyncSession = Depends(get_db_session),
        current_user_id: int | None = Depends(get_current_user_id),
) -> Response:
    """
    Добавление пользователя в список избранных.
    Args:
        request: объект запроса FastAPI.
        user_id: ID целевого пользователя.
        session_db: сессия базы данных из зависимости.
        current_user_id: ID текущего пользователя из зависимости.

    Returns:
        Response: редирект на страницу просмотра полученной карты,
        либо редирект на страницу ошибкой.

    Notes:
        Возможные типы ответов:
        - REDIRECT_WITH_INFO: редирект на страницу профиля целевого пользователя.
        - REDIRECT_WITH_ERROR: редирект на страницу профиля целевого пользователя с ошибкой,
        - NOT_FOUND, UNAUTHORIZED и SERVER_ERROR редирект на страницу с ошибкой.
    """

    use_case = AddFavoriteUserUseCase(session_db)
    data: ToggleFavoriteUserUseCaseResponse = await use_case.execute(current_user_id=current_user_id, target_user_id=user_id)
    if data.response_type == ResponseType.REDIRECT_WITH_INFO:
        url = request.url_for('user_profile', user_id=user_id)
        full_url = f'{url}?success={data.success_message}'
        return RedirectResponse(full_url, status_code=303)

    elif data.response_type == ResponseType.REDIRECT_WITH_ERROR:
        url = request.url_for('user_profile', user_id=user_id)
        full_url = f'{url}?error={data.error_message}'
        return RedirectResponse(full_url, status_code=303)

    else:
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        status_code = RESPONSE_TYPE_TO_HTTP.get(data.response_type, 500)
        url = request.url_for('view_error', error_code=status_code)
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)


@router.post(path='/remove_{user_id}', name='remove_favorite_user')
async def remove_user_favorite(
        request: Request,
        user_id: int,
        session_db: AsyncSession = Depends(get_db_session),
        current_user_id: int | None = Depends(get_current_user_id),
) -> Response:
    """
    Добавление пользователя в список избранных.
    Args:
        request: объект запроса FastAPI.
        user_id: ID целевого пользователя.
        session_db: сессия базы данных из зависимости.
        current_user_id: ID текущего пользователя из зависимости.

    Returns:
        Response: редирект на страницу просмотра полученной карты,
        либо редирект на страницу ошибкой.

    Notes:
        Возможные типы ответов:
        - REDIRECT_WITH_INFO: редирект на страницу профиля целевого пользователя.
        - REDIRECT_WITH_ERROR: редирект на страницу профиля целевого пользователя с ошибкой,
        - NOT_FOUND, UNAUTHORIZED и SERVER_ERROR редирект на страницу с ошибкой.
    """

    use_case = RemoveFavoriteUserUseCase(session_db)
    data: ToggleFavoriteUserUseCaseResponse = await use_case.execute(
        current_user_id=current_user_id, target_user_id=user_id
    )

    if data.response_type == ResponseType.REDIRECT_WITH_INFO:
        url = request.url_for('user_profile', user_id=user_id)
        full_url = f'{url}?success={data.success_message}'
        return RedirectResponse(full_url, status_code=303)

    elif data.response_type == ResponseType.REDIRECT_WITH_ERROR:
        url = request.url_for('user_profile', user_id=user_id)
        full_url = f'{url}?error={data.error_message}'
        return RedirectResponse(full_url, status_code=303)

    else:
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        status_code = RESPONSE_TYPE_TO_HTTP.get(data.response_type, 500)
        url = request.url_for('view_error', error_code=status_code)
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)


@router.post(path='/fight_{user_id}', name='fight_user')
async def fight_user(
        request: Request,
        user_id: int,
        session_db: AsyncSession = Depends(get_db_session),
        current_user_id: int | None = Depends(get_current_user_id),
) -> Response:
    """
    Рейтинговый бой между участниками.
    При успехе не перенаправляет на другие роутеры, а рендерит итог боя тут.
    От повторной отправки защищают внутренние проверки, при обновлении страницы просто будет предупреждение.
    Args:
        request: объект запроса FastAPI.
        user_id: ID целевого пользователя.
        session_db: сессия базы данных из зависимости.
        current_user_id: ID текущего пользователя из зависимости.

    Returns:
        Response: редирект на страницу со стартовым событием, либо на просмотр новой карты,
        либо на страницу ошибки.

    Notes:
        Возможные типы ответов:
        - REDIRECT_WITH_INFO: КОНКРЕТНО ТУТ РЕНДЕРИТ ИТОГ БОЯ.
        - REDIRECT_WITH_ERROR: редирект на страницу получения карты с ошибкой.
        - NOT_FOUND, UNAUTHORIZED и SERVER_ERROR редирект на страницу с ошибкой.
    """

    use_case = ProcessFightUseCase(session_db)
    data: ProcessFightUseCaseResponse = await use_case.execute(user_id=current_user_id, enemy_id=user_id)
    if data.response_type == ResponseType.REDIRECT_WITH_INFO:
        context = {
            'request': request,
            'current_user': data.current_user,
            'fight_dto': data.fight_dto,
        }

        return templates.TemplateResponse(
            request=request,
            name='fights/rating_fight.html',
            context=context,
            status_code=200
        )

    elif data.response_type in (ResponseType.REDIRECT_WITH_ERROR, ResponseType.UNAUTHORIZED):
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        url = request.url_for('user_profile', user_id=user_id)
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)

    else:
        error_msg = data.error_message
        encoded_error = quote(error_msg) if error_msg else ''
        status_code = RESPONSE_TYPE_TO_HTTP.get(data.response_type, 500)
        url = request.url_for('view_error', error_code=status_code)
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)
