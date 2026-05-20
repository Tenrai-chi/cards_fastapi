from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import quote

from cards_app.auth.dependencies import get_current_user_with_profile
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.services.users import user_info_to_dto
from cards_app.types import ViewCardUseCaseDict, ViewGetFreeCardUseCaseDict, GetFreeCardUseCaseDict
from cards_app.use_cases.cards import ViewCardUseCase, ViewGetFreeCardUseCase, GetFreeCardUseCase

from cards_app.models.users import User

router = APIRouter(prefix='/cards', tags=['cards'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get(path='/card-{card_id}', name='view_card')
async def view_card(request: Request,
                    card_id: int,
                    session_db: AsyncSession = Depends(get_db_session),
                    current_user: User | None = Depends(get_current_user_with_profile),
                    error: str = None,
                    success: str = None
                    ):
    """ Просмотр карты """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewCardUseCase(session_db)
    data: ViewCardUseCaseDict = await use_case.execute(card_id, current_user)
    if data.get('card_info_dto') is not None:
        context = {'request': request,
                   'current_user': current_user_dto,
                   'card_dto': data.get('card_info_dto'),
                   'error_message': error,
                   'success_message': success
                   }
        return templates.TemplateResponse(request=request,
                                          name='cards/card.html',
                                          context=context,
                                          status_code=data.get('status_code'))
    else:
        if data.get('status_code') in (404, 500):
            context = {'error': data.get('error_message'),
                       'error_code': data.get('status_code')}
            return templates.TemplateResponse(request=request,
                                              name='errors/error_page.html',
                                              context=context,
                                              status_code=data.get('status_code')
                                              )


@router.get(path='/free_card', name='get_card')
async def view_free_card(request: Request,
                         session_db: AsyncSession = Depends(get_db_session),
                         current_user: User | None = Depends(get_current_user_with_profile),
                         error: str = None
                         ):
    """ Просмотр страницы получения бесплатной случайной карты """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewGetFreeCardUseCase(session_db)
    data: ViewGetFreeCardUseCaseDict = await use_case.execute(current_user)

    context = {'request': request,
               'current_user': current_user_dto,
               'info_dto': data.get('get_free_card_dto'),
               'error_message': error
               }
    return templates.TemplateResponse(request=request,
                                      name='cards/free_card_page.html',
                                      context=context,
                                      status_code=data.get('status_code'))


@router.post(path='/generate_new_card', name='create_card')
async def get_free_card(request: Request,
                        session_db: AsyncSession = Depends(get_db_session),
                        current_user: User | None = Depends(get_current_user_with_profile),
                        ):
    """ Обработка запроса получения бесплатной карты """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = GetFreeCardUseCase(session_db)
    data: GetFreeCardUseCaseDict = await use_case.execute(current_user)

    if data.get('success') is True:
        new_card_id = data.get('new_card_id')
        url = request.url_for('view_card', card_id=new_card_id)
        return RedirectResponse(url, status_code=data.get('status_code'))
    else:
        if data.get('status_code') in (404, 500):
            context = {'error': data.get('error_message'),
                       'status_code': data.get('status_code'),
                       'current_user': current_user_dto}
            return templates.TemplateResponse(request=request,
                                              name='errors/error_page.html',
                                              context=context,
                                              status_code=data.get('status_code')
                                              )
        else:
            error_msg = data['error_message']
            encoded_error = quote(error_msg)
            url = request.url_for('get_card')
            full_url = f'{url}?error={encoded_error}'
            return RedirectResponse(full_url, status_code=303)
