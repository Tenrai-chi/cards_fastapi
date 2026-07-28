from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import quote

from cards_app.auth.dependencies import get_current_user_with_profile, get_current_user_id
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.routers.response_mapping import RESPONSE_TYPE_TO_HTTP, get_error_template
from cards_app.schemas.response import ViewInventoryUseCaseResponse, SaleAmuletUseCaseResponse
from cards_app.services.users import user_info_to_dto
from cards_app.models.users import User
from cards_app.use_cases.inventory import ViewInventoryUseCase, SaleAmuletUseCase
from cards_app.utils.response_types import ResponseType

router = APIRouter(prefix='/inventory', tags=['inventory'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get(path='/{inventory_filter}', name='inventory')
async def inventory(
        request: Request,
        session_db: AsyncSession = Depends(get_db_session),
        current_user: User | None = Depends(get_current_user_with_profile),
        inventory_filter: str = 'all',
        error: str = None,
        success: str = None
) -> Response:
    """
    Просмотр инвентаря пользователя.
    Args:
        request: объект запроса FastAPI.
        session_db: сессия базы данных из зависимости.
        current_user: текущий пользователь из зависимости.
        inventory_filter: фильтр для вывода.
        error: сообщение об ошибке из query-параметра.
        success: сообщение об успехе из query-параметра.

    Returns:
        Response: рендеринг страницы при успехе или рендеринг страницы с ошибкой.

    Notes:
        Возможные типы ответов:
        - SUCCESS: рендеринг данных.
        - UNAUTHORIZED: рендеринг страницы с ошибкой.
        - BAD_REQUEST: ошибка фильтра.
        - SERVER_ERROR: рендеринг страницы ошибки.
    """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewInventoryUseCase(session_db)
    data: ViewInventoryUseCaseResponse = await use_case.execute(
        current_user=current_user,
        inventory_filter=inventory_filter
    )
    if data.response_type == ResponseType.SUCCESS:
        context = {
            'request': request,
            'current_user': current_user_dto,
            'inventory_dto': data.inventory,
            'error_message': error,
            'success_message': success,
            'current_inventory_filter': inventory_filter
        }

        return templates.TemplateResponse(
            request=request,
            name='inventory/inventory.html',
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


@router.post(path='/sell_amulet/{amulet_id}', name='sell_amulet')
async def sell_amulet(
        request: Request,
        amulet_id: int,
        session_db: AsyncSession = Depends(get_db_session),
        current_user_id: int | None = Depends(get_current_user_id),
) -> Response:
    """
    Продажа амулета из инвентаря пользователя.
    Args:
        request: объект запроса FastAPI.
        amulet_id: ID амулета.
        session_db: сессия базы данных из зависимости.
        current_user_id: ID текущего пользователя из зависимости.

    Returns:
        Response: рендеринг страницы при успехе или рендеринг страницы с ошибкой.

    Notes:
        Возможные типы ответов:
        - REDIRECT_WITH_INFO: редирект в инвентарь при успешной продаже.
        - REDIRECT_WITH_ERROR: редирект в инвентарь при какой-то ошибке.
        - UNAUTHORIZED, FORBIDDEN NOT_FOUND и SERVER_ERROR: редирект на страницу ошибки.
    """

    use_case = SaleAmuletUseCase(session_db)
    data: SaleAmuletUseCaseResponse = await use_case.execute(current_user_id=current_user_id, amulet_id=amulet_id)
    if data.response_type == ResponseType.REDIRECT_WITH_INFO:
        success_msg = data.success_message
        encoded_success = quote(success_msg)
        url = request.url_for('inventory', inventory_filter='amulets')
        full_url = f'{url}?success={encoded_success}'
        return RedirectResponse(full_url, status_code=303)

    elif data.response_type == ResponseType.REDIRECT_WITH_ERROR:
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        url = request.url_for('inventory', inventory_filter='amulets')
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)

    else:
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        status_code = RESPONSE_TYPE_TO_HTTP.get(data.response_type, 500)
        url = request.url_for('view_error', error_code=status_code)
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)
