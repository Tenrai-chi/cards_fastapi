from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import quote

from cards_app.auth.dependencies import get_current_user_with_profile
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.services.users import user_info_to_dto
from cards_app.use_cases.cards import BuyStoreCardUseCase

from cards_app.models.users import User
from cards_app.use_cases.store import ViewCardStoreUseCase

router = APIRouter(prefix='/store', tags=['store'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get(path='/cards', name='card_store')
async def view_card_store(request: Request,
                          session_db: AsyncSession = Depends(get_db_session),
                          current_user: User | None = Depends(get_current_user_with_profile),
                          error: str = None
                          ):
    """ Просмотр страницы магазина карт """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewCardStoreUseCase(session_db)
    try:
        card_store_dto = await use_case.execute()
    except Exception as error:
        return templates.TemplateResponse(
            request=request,
            name='error_page.html',
            context={'error': error, 'error_code': 500},
            status_code=500
        )

    context = {'request': request,
               'current_user': current_user_dto,
               'card_store_dto': card_store_dto,
               'error_message': error
               }

    return templates.TemplateResponse(request, 'card_store.html', context)


@router.post(path='/cards/buy-{card_id}', name='buy_card_in_store')
async def buy_card_in_store(request: Request,
                            session_db: AsyncSession = Depends(get_db_session),
                            current_user: User | None = Depends(get_current_user_with_profile),
                            card_id: int = None
                            ):
    """ Покупка в магазине карт """

    use_case = BuyStoreCardUseCase(session_db)
    try:
        data: dict = await use_case.execute(current_user, card_id)
        if data.get('error_message'):
            error_msg = data['error_message']
            encoded_error = quote(error_msg)
            url = request.url_for('card_store')
            full_url = f'{url}?error={encoded_error}'
            return RedirectResponse(full_url, status_code=303)
        else:
            new_card_id = data['new_card_id']
            url = request.url_for('view_card', card_id=new_card_id)
            return RedirectResponse(url, status_code=303)
    except Exception as error:
        return templates.TemplateResponse(
            request=request,
            name='error_page.html',
            context={'error': error, 'error_code': 500},
            status_code=500
        )
