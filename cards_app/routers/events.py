from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.config.settings import settings
from cards_app.config.database import get_db_session
from cards_app.auth.dependencies import get_current_user_with_profile
from cards_app.use_cases.events import ViewNewsUseCase
from cards_app.services.users import user_info_to_dto
from cards_app.config.exceptions import *

from cards_app.models.users import User

router = APIRouter(prefix='', tags=[''])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get('/news')
async def view_news(request: Request,
                    session_db: AsyncSession = Depends(get_db_session),
                    current_user: User | None = Depends(get_current_user_with_profile),
                    page: int = 1,
                    size: int = 6
                    ):
    """ Просмотр новостей """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewNewsUseCase(session_db)
    news_dto = await use_case.execute(page, size)  # тут будет вызов NewsTDO

    context = {'request': request,
               'current_user': current_user_dto,
               'news': news_dto
               }
    return templates.TemplateResponse(request, 'home_news.html', context)
