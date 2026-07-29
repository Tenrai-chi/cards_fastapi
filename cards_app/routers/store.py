from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import quote

from cards_app.auth.dependencies import get_current_user_with_profile, get_current_user_id
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.routers.response_mapping import RESPONSE_TYPE_TO_HTTP, get_error_template
from cards_app.schemas.response import (
    ViewCardStoreUseCaseResponse, ViewItemStoreUseCaseResponse,
    BuyStoreCardUseCaseResponse, BuyBoxUseCaseResponse, BuyItemUseCaseResponse
)
from cards_app.services.users import user_info_to_dto
from cards_app.use_cases.store import (
    BuyStoreCardUseCase, ViewItemStoreUseCase, BuyBoxUseCase, BuyExpItemUseCase,
    BuyAmuletUseCase, BuyUpgradeItemUseCase
)

from cards_app.models.users import User
from cards_app.use_cases.store import ViewCardStoreUseCase
from cards_app.utils.response_types import ResponseType

router = APIRouter(prefix='/store', tags=['store'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get(path='/cards', name='card_store')
async def view_card_store(
        request: Request,
        session_db: AsyncSession = Depends(get_db_session),
        current_user: User | None = Depends(get_current_user_with_profile),
        error: str = None
) -> Response:
    """
    Просмотр страницы магазина карт.
    Args:
        request: объект запроса FastAPI.
        session_db: сессия базы данных из зависимости.
        current_user: текущий пользователь из зависимости.
        error: сообщение об ошибке из query-параметра.

    Returns:
        Response: рендеринг страницы при успехе или рендеринг страницы с ошибкой.

    Notes:
        Возможные типы ответов:
        - SUCCESS: рендеринг данных.
        - SERVER_ERROR: рендеринг страницы ошибки.
    """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewCardStoreUseCase(session_db)
    data: ViewCardStoreUseCaseResponse = await use_case.execute()

    if data.response_type == ResponseType.SUCCESS:
        context = {
            'request': request,
            'current_user': current_user_dto,
            'card_store_dto': data.card_store,
            'error_message': error,
        }

        return templates.TemplateResponse(
            request=request,
            name='store/card_store.html',
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


@router.get(path='/items/{store_filter}', name='item_store')
async def view_items_store(
        request: Request,
        session_db: AsyncSession = Depends(get_db_session),
        current_user: User | None = Depends(get_current_user_with_profile),
        store_filter: str = 'all',
        error: str = None
) -> Response:
    """
    Просмотр страницы магазина карт.
    Args:
        request: объект запроса FastAPI.
        session_db: сессия базы данных из зависимости.
        current_user: текущий пользователь из зависимости.
        store_filter: фильтр магазина, по умолчанию all.
        error: сообщение об ошибке из query-параметра.

    Returns:
        Response: рендеринг страницы при успехе или рендеринг страницы с ошибкой.

    Notes:
        Возможные типы ответов:
        - SUCCESS: рендеринг данных.
        - BAD_REQUEST: неправильный параметр фильтра магазина.
        - SERVER_ERROR: рендеринг страницы ошибки.
    """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewItemStoreUseCase(session_db)
    data: ViewItemStoreUseCaseResponse = await use_case.execute(store_filter=store_filter)
    if data.response_type == ResponseType.SUCCESS:
        context = {
            'request': request,
            'current_user': current_user_dto,
            'store_dto': data.store,
            'error_message': error,
            'current_store_filter': store_filter
        }
        return templates.TemplateResponse(
            request=request,
            name='store/item_store.html',
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


@router.post(path='/cards/buy-{card_id}', name='buy_card_in_store')
async def buy_card_in_store(
        request: Request,
        session_db: AsyncSession = Depends(get_db_session),
        current_user_id: int | None = Depends(get_current_user_id),
        card_id: int = None
) -> Response:
    """
    Покупка в магазине карт.
    Args:
        request: объект запроса FastAPI.
        session_db: сессия базы данных из зависимости.
        current_user_id: ID текущего пользователя из зависимости.
        card_id: ID карты-шаблона из магазина.

    Returns:
        Response: рендеринг страницы с получением бесплатной карты.
    Notes:
        Возможные типы ответов:
        - REDIRECT_WITH_INFO: редирект к обновленным данным.
        - REDIRECT_WITH_ERROR, UNAUTHORIZED: редирект на страницу магазина карт,
        - SERVER_ERROR редирект на страницу с ошибкой.
    """

    use_case = BuyStoreCardUseCase(session_db)
    data: BuyStoreCardUseCaseResponse = await use_case.execute(current_user_id=current_user_id, temp_card_id=card_id)

    if data.response_type == ResponseType.REDIRECT_WITH_INFO:
        new_card_id = data.new_card_id
        url = request.url_for('view_card', card_id=new_card_id)
        return RedirectResponse(url, status_code=303)

    elif data.response_type in (ResponseType.REDIRECT_WITH_ERROR, ResponseType.UNAUTHORIZED):
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        url = request.url_for('card_store')
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)

    else:
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        status_code = RESPONSE_TYPE_TO_HTTP.get(data.response_type, 500)
        url = request.url_for('view_error', error_code=status_code)
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)


@router.post(path='/open/box-{box_id}', name='buy_box_in_store')
async def buy_box_in_store(
        request: Request,
        session_db: AsyncSession = Depends(get_db_session),
        current_user_id: int | None = Depends(get_current_user_id),
        box_id: int = None
) -> Response:
    """
    Покупка сундука в магазине.
    Args:
        request: объект запроса FastAPI.
        session_db: сессия базы данных из зависимости.
        current_user_id: ID текущего пользователя из зависимости.
        box_id: ID сундука.

    Returns:
        Response: редирект на просмотр карты,
        либо редирект с преобразованием данных и сохранением в сессию при открытии сундука.
        либо редирект на страницу ошибкой.

    Notes:
        Возможные типы ответов:
        - REDIRECT_WITH_INFO: редирект к просмотру полученных предметов или карте.
        - REDIRECT_WITH_ERROR и UNAUTHORIZED: редирект на страницу магазина с ошибкой.
        - SERVER_ERROR редирект на страницу с ошибкой.
    """

    use_case = BuyBoxUseCase(session_db)
    data: BuyBoxUseCaseResponse = await use_case.execute(current_user_id=current_user_id, box_id=box_id)

    if data.response_type == ResponseType.REDIRECT_WITH_INFO:
        if data.card_id:
            success_msg = data.success_message
            encoded_success = quote(success_msg)
            new_card_id = data.card_id
            url = request.url_for('view_card', card_id=new_card_id)
            full_url = f'{url}?success={encoded_success}'
            return RedirectResponse(full_url, status_code=303)
        else:
            session_data = {
                'exp_items_dto': [item.model_dump() for item in data.exp_items_dto] if data.exp_items_dto else None,
                'amulets_items_dto': [item.model_dump() for item in
                                      data.amulets_items_dto] if data.amulets_items_dto else None,
                'current_user': data.current_user.model_dump() if data.current_user else None,
            }
            request.session['box_result'] = session_data
            url = request.url_for('show_box_result')
            success_msg = data.success_message
            encoded_success = quote(success_msg)
            full_url = f'{url}?success={encoded_success}'
            return RedirectResponse(full_url, status_code=303)

    else:
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        status_code = RESPONSE_TYPE_TO_HTTP.get(data.response_type, 500)
        url = request.url_for('view_error', error_code=status_code)
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)


@router.get(path='/box-result', name='show_box_result')
async def show_box_result(
        request: Request,
        success: str | None = None
) -> Response:
    """
    Показывает результат открытия сундука с предметами.
    После отображения данные из сессии удаляются.
    """

    result = request.session.pop('box_result', None)
    if result is None:
        error_msg = f'Что-то пошло не так, повторите снова'
        encoded_error = quote(error_msg)
        url = request.url_for('item_store', store_filter='all')
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)

    if result.get('exp_items_dto'):
        context = {
            'request': request,
            'current_user': result.get('current_user'),
            'exp_items_dto': result.get('exp_items_dto'),
            'success_message': success
        }
        return templates.TemplateResponse(
            request=request,
            name='store/open_exp_items_box.html',
            context=context,
            status_code=200
        )
    elif result.get('amulets_items_dto'):
        context = {
            'request': request,
            'current_user': result.get('current_user'),
            'amulets_items_dto': result.get('amulets_items_dto'),
            'success_message': success
        }
        return templates.TemplateResponse(
            request=request,
            name='store/open_amulets_box.html',
            context=context,
            status_code=200
        )
    else:
        error_msg = f'Что-то пошло не так, повторите снова'
        encoded_error = quote(error_msg)
        url = request.url_for('item_store', store_filter='all')
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)


@router.post(path='/buy_book/book-{book_id}', name='buy_book_in_store')
async def buy_book_in_store(
        request: Request,
        book_id: int,
        amount: int = Form(...),
        session_db: AsyncSession = Depends(get_db_session),
        current_user_id: int | None = Depends(get_current_user_id),
) -> Response:
    """
    Покупка книги в магазине.
    Args:
        request: объект запроса FastAPI.
        book_id: ID книги.
        amount: количество.
        session_db: сессия базы данных из зависимости.
        current_user_id: ID текущего пользователя из зависимости.

    Returns:
        Response: редирект на страницу просмотра полученной карты,
        либо редирект на страницу ошибкой.

    Notes:
        Возможные типы ответов:
        - REDIRECT_WITH_INFO: редирект к обновленным данным.
        - REDIRECT_WITH_ERROR, UNAUTHORIZED: редирект на страницу получения карты с ошибкой,
        - SERVER_ERROR редирект на страницу с ошибкой.
    """

    use_case = BuyExpItemUseCase(session_db)
    data: BuyItemUseCaseResponse = await use_case.execute(
        current_user_id=current_user_id,
        exp_item_id=book_id,
        amount=amount,
    )

    if data.response_type == ResponseType.REDIRECT_WITH_INFO:
        success_msg = data.success_message
        encoded_success = quote(success_msg)
        url = request.url_for('item_store', store_filter='exp_items')
        full_url = f'{url}?success={encoded_success}'
        return RedirectResponse(full_url, status_code=303)
    elif data.response_type in (ResponseType.REDIRECT_WITH_ERROR, ResponseType.UNAUTHORIZED):
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        url = request.url_for('item_store', store_filter='exp_items')
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)

    else:
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        status_code = RESPONSE_TYPE_TO_HTTP.get(data.response_type, 500)
        url = request.url_for('view_error', error_code=status_code)
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)


@router.post(path='/buy_amulet/amulet-{amulet_id}', name='buy_amulet_in_store')
async def buy_amulet_in_store(
        request: Request,
        amulet_id: int,
        session_db: AsyncSession = Depends(get_db_session),
        current_user_id: int | None = Depends(get_current_user_id),
) -> Response:
    """
    Покупка амулета в магазине.
    Args:
        request: объект запроса FastAPI.
        amulet_id: ID амулета.
        session_db: сессия базы данных из зависимости.
        current_user_id: ID текущего пользователя из зависимости.

    Returns:
        Response: редирект на страницу просмотра полученной карты,
        либо редирект на страницу ошибкой.

    Notes:
        Возможные типы ответов:
        - REDIRECT_WITH_INFO: редирект к обновленным данным.
        - REDIRECT_WITH_ERROR, UNAUTHORIZED: редирект на страницу получения карты с ошибкой,
        - SERVER_ERROR редирект на страницу с ошибкой.
    """

    use_case = BuyAmuletUseCase(session_db)
    data: BuyItemUseCaseResponse = await use_case.execute(current_user_id=current_user_id, amulet_id=amulet_id)

    if data.response_type == ResponseType.REDIRECT_WITH_INFO:
        success_msg = data.success_message
        encoded_success = quote(success_msg)
        url = request.url_for('item_store', store_filter='amulet')
        full_url = f'{url}?success={encoded_success}'
        return RedirectResponse(full_url, status_code=303)

    elif data.response_type in (ResponseType.REDIRECT_WITH_ERROR, ResponseType.UNAUTHORIZED):
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        url = request.url_for('item_store', store_filter='amulet')
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)

    else:
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        status_code = RESPONSE_TYPE_TO_HTTP.get(data.response_type, 500)
        url = request.url_for('view_error', error_code=status_code)
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)


@router.post(path='/buy_upgrade_item/upgrade_item-{upgrade_item_id}', name='buy_upgrade_item_in_store')
async def buy_upgrade_item_in_store(
        request: Request,
        upgrade_item_id: int,
        session_db: AsyncSession = Depends(get_db_session),
        current_user_id: int | None = Depends(get_current_user_id),
) -> Response:
    """
    Покупка амулета в магазине.
    Args:
        request: объект запроса FastAPI.
        upgrade_item_id: ID предмета усиления.
        session_db: сессия базы данных из зависимости.
        current_user_id: ID текущего пользователя из зависимости.

    Returns:
        Response: редирект на страницу просмотра полученной карты,
        либо редирект на страницу ошибкой.

    Notes:
        Возможные типы ответов:
        - REDIRECT_WITH_INFO: редирект к обновленным данным.
        - REDIRECT_WITH_ERROR, UNAUTHORIZED: редирект на страницу получения карты с ошибкой,
        - SERVER_ERROR редирект на страницу с ошибкой.
    """

    use_case = BuyUpgradeItemUseCase(session_db)
    data: BuyItemUseCaseResponse = await use_case.execute(current_user_id=current_user_id, upgrade_item_id=upgrade_item_id)

    if data.response_type == ResponseType.REDIRECT_WITH_INFO:
        success_msg = data.success_message
        encoded_success = quote(success_msg)
        url = request.url_for('item_store', store_filter='upgrade_item')
        full_url = f'{url}?success={encoded_success}'
        return RedirectResponse(full_url, status_code=303)

    elif data.response_type in (ResponseType.REDIRECT_WITH_ERROR, ResponseType.UNAUTHORIZED):
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        url = request.url_for('item_store', store_filter='upgrade_item')
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)

    else:
        error_msg = data.error_message
        encoded_error = quote(error_msg)
        status_code = RESPONSE_TYPE_TO_HTTP.get(data.response_type, 500)
        url = request.url_for('view_error', error_code=status_code)
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)
