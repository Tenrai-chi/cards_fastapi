from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from cards_app.auth.dependencies import get_current_user_with_profile
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.models.users import User
from cards_app.services.users import user_info_to_dto
from cards_app.use_cases.events import ViewNewsUseCase


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

    try:
        current_user_dto = await user_info_to_dto(current_user)
        use_case = ViewNewsUseCase(session_db)
        news_dto = await use_case.execute(page, size)

        context = {'request': request,
                   'current_user': current_user_dto,
                   'news': news_dto
                   }
        return templates.TemplateResponse(request=request,
                                          name='home_news.html',
                                          context=context,
                                          status_code=200)
    except Exception as error:
        return templates.TemplateResponse(request=request,
                                          name='error_page.html',
                                          context={'error': error, 'error_code': 500},
                                          status_code=500
                                          )
