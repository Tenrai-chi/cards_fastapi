from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.auth.db_utils import delete_refresh_token
from ..services.auth import create_user_and_profile, authenticate_and_create_tokens

router = APIRouter(prefix='/auth', tags=['auth'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get('/register')
def register_page(request: Request):
    """ Выводит форму регистрации """

    return templates.TemplateResponse(request=request, name='register.html', context={'request': request})


@router.post('/register')
async def register(request: Request,
                   username: str = Form(...),
                   email: str = Form(...),
                   password: str = Form(...),
                   db_session: AsyncSession = Depends(get_db_session)):
    """ Обработчик формы регистрации.
        При успешной регистрации перенаправляет на страницу входа.
    """

    result: dict = await create_user_and_profile(db_session, username, email, password)
    if result['error_message']:
        return templates.TemplateResponse(request=request,
                                          name='register.html',
                                          context={'request': request, 'error': result['error_message']}
                                          )

    return RedirectResponse(url='/auth/login', status_code=303)


@router.get('/login')
async def login_page(request: Request):
    """ Выводит форму входа в систему """

    return templates.TemplateResponse(request=request, name='login.html', context={'request': request})


@router.post('/login')
async def login(request: Request,
                username: str = Form(...),
                password: str = Form(...),
                db_session: AsyncSession = Depends(get_db_session)):
    """ Обрабатывает форму входа в систему """

    result: dict = await authenticate_and_create_tokens(db_session, username, password)
    if result['error_message']:
        return templates.TemplateResponse(request=request,
                                          name='login.html',
                                          context={'request': request, 'error': result['error_message']})

    user = result['user']
    response = RedirectResponse(url=f'/users/{user.id}', status_code=303)
    response.set_cookie(key='access_token',
                        value=result['access_token'],
                        httponly=True,
                        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                        secure=False, samesite='lax')
    response.set_cookie(key='refresh_token',
                        value=result['refresh_token'],
                        httponly=True,
                        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
                        secure=False, samesite='lax')
    return response


@router.get('/logout')
async def logout(request: Request, db_session: AsyncSession = Depends(get_db_session)):
    """ Выполняет выход пользователя из системы и удаляет куки с токенами """

    refresh_token = request.cookies.get('refresh_token')
    if refresh_token:
        await delete_refresh_token(db_session, refresh_token)
    response = RedirectResponse(url='/auth/login', status_code=303)
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response
