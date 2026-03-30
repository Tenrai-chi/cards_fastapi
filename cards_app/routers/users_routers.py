from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from cards_app.models import User

from cards_app.config.security import decode_token
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings

router = APIRouter(prefix='/users', tags=['users'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get('/profile')
async def get_profile(request: Request, db: AsyncSession = Depends(get_db_session)):
    """ Страница профиля текущего пользователя """

    access_token = request.cookies.get('access_token')
    if not access_token:
        return RedirectResponse(url='/auth/login', status_code=303)

    payload = decode_token(access_token, expected_type='access')
    if not payload:
        return RedirectResponse(url='/auth/login', status_code=303)

    user_id = int(payload.get('sub'))
    result = await db.execute(select(User).options(selectinload(User.profile)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return RedirectResponse(url='/auth/login', status_code=303)

    return templates.TemplateResponse(request=request,
                                      name='profile.html',
                                      context={'request': request, 'user': user})


@router.get('/{user_id}')
async def user_profile(request: Request,
                       user_id: int,
                       db: AsyncSession = Depends(get_db_session)):
    """
        Страница профиля пользователя по ID. Доступна всем, без авторизации.
        Если пользователь не найден – 404.
    """

    result = await db.execute(select(User).options(selectinload(User.profile)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return templates.TemplateResponse(request=request,
                                          name="404.html",
                                          context={"request": request, "error": "Пользователь не найден"},
                                          status_code=404
                                          )
    return templates.TemplateResponse(request=request,
                                      name="profile.html",
                                      context={"request": request, "user": user}
                                      )
