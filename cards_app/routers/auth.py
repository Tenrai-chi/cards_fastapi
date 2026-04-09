from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.auth.db_utils import delete_refresh_token
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.services.auth import create_user_and_profile, authenticate_and_create_tokens

router = APIRouter(prefix='/auth', tags=['auth'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get(path='/register', name='register_page')
async def register_page(request: Request):
    """ Отображает страницу регистрации """

    return templates.TemplateResponse(request=request,
                                      name='register.html',
                                      context={'request': request},
                                      status_code=200)


@router.post(path='/register', name='register')
async def register(request: Request,
                   username: str = Form(...),
                   email: str = Form(...),
                   password: str = Form(...),
                   db_session: AsyncSession = Depends(get_db_session)):
    """ Обрабатывает форму регистрации.
        При успехе перенаправляет на страницу входа, при ошибке возвращает форму с сообщением об ошибке.
    """

    result: dict = await create_user_and_profile(db_session, username, email, password)
    if result['error_message']:
        return templates.TemplateResponse(request=request,
                                          name='register.html',
                                          context={'request': request, 'error': result['error_message']},
                                          status_code=200
                                          )

    url = request.url_for('login_page')
    return RedirectResponse(url, status_code=303)


@router.get(path='/login', name='login_page')
async def login_page(request: Request):
    """ Отображает форму входа """

    return templates.TemplateResponse(request=request,
                                      name='login.html',
                                      context={'request': request},
                                      status_code=200)


@router.post(path='/login', name='login')
async def login(request: Request,
                username: str = Form(...),
                password: str = Form(...),
                db_session: AsyncSession = Depends(get_db_session)):
    """ Обрабатывает форму входа в систему.
        При успехе устанавливает refresh_token и перенаправляет на страницу входа
        При ошибке возвращает форму с сообщением об ошибке.
    """

    result: dict = await authenticate_and_create_tokens(db_session, username, password)
    if result['error_message']:
        return templates.TemplateResponse(request=request,
                                          name='login.html',
                                          context={'request': request, 'error': result['error_message']},
                                          status_code=200)

    user = result['user']
    url = request.url_for('user_profile', user_id=user.id)
    response = RedirectResponse(url=url, status_code=303)
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


@router.get(path='/logout', name='logout')
async def logout(request: Request, db_session: AsyncSession = Depends(get_db_session)):
    """ Выполняет выход пользователя из системы и удаляет куки с токенами """

    refresh_token = request.cookies.get('refresh_token')
    if refresh_token:
        await delete_refresh_token(db_session, refresh_token)

    url = request.url_for('login_page')
    response = RedirectResponse(url=url, status_code=303)
    response.delete_cookie(key='access_token', secure=False, samesite='lax')
    response.delete_cookie(key='refresh_token', secure=False, samesite='lax')

    return response
