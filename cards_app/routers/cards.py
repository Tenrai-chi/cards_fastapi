from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.config.settings import settings
from cards_app.config.database import get_db_session
from cards_app.auth.dependencies import get_current_user_with_profile
from cards_app.use_cases.cards import ViewCardUseCase
from cards_app.services.users import user_info_to_dto
from cards_app.config.exceptions import *

from cards_app.models.users import User

router = APIRouter(prefix='/cards', tags=['cards'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get('/free_card')
async def get_free_card(request: Request,
                        user_id: int,
                        session_db: AsyncSession = Depends(get_db_session),
                        current_user: User | None = Depends(get_current_user_with_profile),
                        ):
    """ Просмотр страницы с получением бесплатной карты """
    pass


@router.post('/generate_new_card')
async def get_free_card(request: Request,
                        user_id: int,
                        session_db: AsyncSession = Depends(get_db_session),
                        current_user: User | None = Depends(get_current_user_with_profile),
                        ):
    """ Обработка запроса получения случайной карты """
    pass


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
