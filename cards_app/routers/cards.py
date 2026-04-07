from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import quote

from cards_app.config.settings import settings
from cards_app.config.database import get_db_session
from cards_app.auth.dependencies import get_current_user_with_profile
from cards_app.use_cases.cards import ViewCardUseCase, ViewGetFreeCard, GetFreeCardUseCase
from cards_app.services.users import user_info_to_dto
from cards_app.config.exceptions import *

from cards_app.models.users import User

router = APIRouter(prefix='/cards', tags=['cards'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get('/card-{card_id}')
async def view_card(request: Request,
                    card_id: int,
                    session_db: AsyncSession = Depends(get_db_session),
                    current_user: User | None = Depends(get_current_user_with_profile),
                    ):
    """ Просмотр карты """

    use_case = ViewCardUseCase(session_db)
    current_user_dto = await user_info_to_dto(current_user)
    try:
        card_dto = await use_case.execute(card_id, current_user)
    except CardNotFoundError:
        return templates.TemplateResponse(
            request=request,
            name='error_page.html',
            context={'error': 'Карта не найдена', 'error_code': 404},
            status_code=404
        )

    context = {'request': request,
               'current_user': current_user_dto,
               'card_dto': card_dto,
               }
    return templates.TemplateResponse(request, 'card.html', context)


@router.get('/free_card')
async def view_free_card(request: Request,
                         session_db: AsyncSession = Depends(get_db_session),
                         current_user: User | None = Depends(get_current_user_with_profile),
                         error: str = None
                         ):
    """ Просмотр страницы получения бесплатной случайной карты """

    use_case = ViewGetFreeCard(session_db)
    current_user_dto = await user_info_to_dto(current_user)
    try:
        info_dto = await use_case.execute()
    except Exception as error:
        return templates.TemplateResponse(
            request=request,
            name='error_page.html',
            context={'error': error, 'error_code': 500},  # Произошла какая-то залупа
            status_code=500
        )

    context = {'request': request,
               'current_user': current_user_dto,
               'info_dto': info_dto,
               'error_message': error
               }

    return templates.TemplateResponse(request, 'free_card_page.html', context)


@router.post('/generate_new_card')
async def get_free_card(request: Request,
                        session_db: AsyncSession = Depends(get_db_session),
                        current_user: User | None = Depends(get_current_user_with_profile),
                        ):
    """ Обработка запроса получения бесплатной карты """

    use_case = GetFreeCardUseCase(session_db)
    data: dict = await use_case.execute(current_user)
    if data.get('error_message'):
        error_msg = data['error_message']
        encoded_error = quote(error_msg)
        return RedirectResponse(url=f'/cards/free_card?error={encoded_error}', status_code=303)
    else:
        new_card_id = data['new_card_id']
        return RedirectResponse(url=f'/cards/card-{new_card_id}', status_code=303)
