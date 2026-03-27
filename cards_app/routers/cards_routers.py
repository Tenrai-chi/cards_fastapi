from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.models import ClassCard

router = APIRouter(prefix='/class-cards', tags=['class_cards'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get('')
async def show_class_cards(request: Request, session: AsyncSession = Depends(get_db_session)):
    """ Тестовый эндпоинт """

    result = await session.execute(select(ClassCard))
    cards = result.scalars().all()
    cards_data = []
    for card in cards:
        cards_data.append({
            'id': card.id,
            'name': card.name,
            'skill': card.skill,
            'description': card.description,
            'description_for_history_fight': card.description_for_history_fight,
            'numeric_value': card.numeric_value,
            'chance_use': card.chance_use,
            'image_url': f'{settings.STATIC_URL}/{card.image}',
        })
    return templates.TemplateResponse(request=request, name='class_cards.html', context={'cards': cards_data})
