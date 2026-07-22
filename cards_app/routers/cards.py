import json
from json import JSONDecodeError

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import quote

from cards_app.auth.dependencies import get_current_user_with_profile, get_current_user_id
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.schemas.response import (
    ViewCardUseCaseResponse, ViewGetFreeCardUseCaseResponse,
    GetFreeCardUseCaseResponse, ViewUserCardsUseResponse, ViewTradingUseCaseResponse, ViewMergeUseCaseResponse,
    MergeUseCaseResponse
)
from cards_app.services.users import user_info_to_dto
from cards_app.types import (
                             ViewUpgradeUseCaseDict, UpgradeUseCaseDict)
from cards_app.use_cases.cards import (ViewCardUseCase, ViewGetFreeCardUseCase, GetFreeCardUseCase,
                                       ViewUserCardsUseCase, ViewTradingUseCase, ViewMergeUseCase,
                                       MergeUseCase, ViewUpgradeUseCase, UpgradeUseCase)

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
    """ Просмотр конкретной карты """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewCardUseCase(session_db)
    data: ViewCardUseCaseResponse = await use_case.execute(card_id, current_user)
    if data.card_info is not None:
        context = {
            'request': request,
            'current_user': current_user_dto,
            'card_dto': data.card_info,
            'error_message': error,
            'success_message': success
        }
        return templates.TemplateResponse(
            request=request,
            name='cards/card.html',
            context=context,
            status_code=data.status_code
        )
    else:
        if data.status_code in (404, 500):
            context = {
                'error': data.error_message,
                'error_code': data.status_code,
                'current_user': current_user_dto
            }
            return templates.TemplateResponse(
                request=request,
                name='errors/error_page.html',
                context=context,
                status_code=data.status_code
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
    data: ViewGetFreeCardUseCaseResponse = await use_case.execute(current_user)

    context = {
        'request': request,
        'current_user': current_user_dto,
        'info_dto': data.get_free_card,
        'error_message': error
    }
    return templates.TemplateResponse(
        request=request,
        name='cards/free_card_page.html',
        context=context,
        status_code=data.status_code
    )


@router.post(path='/generate_new_card', name='create_card')
async def get_free_card(request: Request,
                        session_db: AsyncSession = Depends(get_db_session),
                        current_user_id: int | None = Depends(get_current_user_id),
                        ):
    """ Обработка запроса на получение бесплатной карты """

    use_case = GetFreeCardUseCase(session_db)
    data: GetFreeCardUseCaseResponse = await use_case.execute(current_user_id)

    if data.success is True:
        new_card_id = data.new_card_id
        url = request.url_for('view_card', card_id=new_card_id)
        return RedirectResponse(url, status_code=data.status_code)
    else:
        if data.status_code == 500:
            context = {
                'error': data.error_message,
                'status_code': data.status_code,
                'current_user': data.current_user_dto
            }
            return templates.TemplateResponse(
                request=request,
                name='errors/error_page.html',
                context=context,
                status_code=data.status_code
            )
        else:
            error_msg = data.error_message
            encoded_error = quote(error_msg)
            url = request.url_for('get_card')
            full_url = f'{url}?error={encoded_error}'
            return RedirectResponse(full_url, status_code=303)


@router.get(path='/user-{user_id}', name='view_user_cards')
async def view_user_cards(request: Request,
                          user_id: int,
                          session_db: AsyncSession = Depends(get_db_session),
                          current_user: User | None = Depends(get_current_user_with_profile),
                          ):
    """ Просмотр всех карт пользователя """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewUserCardsUseCase(session_db)
    data: ViewUserCardsUseResponse = await use_case.execute(user_id)
    if data.user_cards is not None:
        context = {
            'request': request,
            'current_user': current_user_dto,
            'user_cards_dto': data.user_cards,
        }
        return templates.TemplateResponse(
            request=request,
            name='cards/user_cards.html',
            context=context,
            status_code=data.status_code
        )
    else:
        if data.status_code in (404, 500):
            context = {'error': data.error_message,
                       'error_code': data.status_code,
                       'current_user': current_user_dto}
            return templates.TemplateResponse(
                request=request,
                name='errors/error_page.html',
                context=context,
                status_code=data.status_code
            )


@router.get(path='/trading', name='trading')
async def view_trading(request: Request,
                       session_db: AsyncSession = Depends(get_db_session),
                       current_user: User | None = Depends(get_current_user_with_profile),
                       error: str = None,
                       success: str = None
                       ):
    """ Просмотр торговой площадки с картами """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewTradingUseCase(session_db)
    data: ViewTradingUseCaseResponse = await use_case.execute()
    if data.cards_trading is not None:
        context = {
            'request': request,
            'current_user': current_user_dto,
            'cards_trading_dto': data.cards_trading,
            'error_message': error,
            'success_message': success
        }
        return templates.TemplateResponse(
            request=request,
            name='cards/trading.html',
            context=context,
            status_code=data.status_code
        )
    else:
        # todo сделать нормальный вывод ошибки и почему она происходит
        context = {
            'error': 'Какая-то ошибка',
            'error_code': 500,
            'current_user': current_user_dto
        }
        return templates.TemplateResponse(
            request=request,
            name='errors/error_page.html',
            context=context,
            status_code=data.status_code
        )


@router.get(path='/card-{card_id}/merge_menu', name='view_merge_card')
async def view_merge_card(request: Request,
                          card_id: int,
                          session_db: AsyncSession = Depends(get_db_session),
                          current_user: User | None = Depends(get_current_user_with_profile),
                          error: str = None,
                          success: str = None
                          ):
    """ Просмотр меню слияния карты """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewMergeUseCase(session_db)
    data: ViewMergeUseCaseResponse = await use_case.execute(current_card_id=card_id,
                                                            current_user=current_user)
    if data.merge is not None:
        context = {
            'request': request,
            'current_user': current_user_dto,
            'merge_dto': data.merge,
            'error_message': error,
            'success_message': success
        }
        return templates.TemplateResponse(
            request=request,
            name='cards/merge_menu.html',
            context=context,
            status_code=data.status_code
        )
    else:
        if data.status_code in (400, 404, 500):
            context = {
                'error': data.error_message,
                'error_code': data.status_code,
                'current_user': current_user_dto
            }
            return templates.TemplateResponse(
                request=request,
                name='errors/error_page.html',
                context=context,
                status_code=data.status_code
            )


@router.post('/merge', name='merge_cards')
async def merge_cards(request: Request,
                      main_card_id: int = Form(...),
                      sacrificed_ids: str = Form(...),
                      session_db: AsyncSession = Depends(get_db_session),
                      current_user_id: int | None = Depends(get_current_user_id)):
    """ Обработка запроса на повышение уровня слияния карты """

    try:
        cards_for_merge = [int(card_id) for card_id in json.loads(sacrificed_ids)]
    except (JSONDecodeError, ValueError, TypeError) as _:
        cards_for_merge = []
    use_case = MergeUseCase(session_db=session_db)
    data: MergeUseCaseResponse = await use_case.execute(current_user_id=current_user_id,
                                                        current_card_id=main_card_id,
                                                        cards_for_merge=cards_for_merge
                                                        )
    if data.success is True:
        success_msg = data.success_message
        encoded_success = quote(success_msg)
        url = request.url_for('view_card', card_id=main_card_id)
        full_url = f'{url}?success={encoded_success}'
        return RedirectResponse(full_url, status_code=data.status_code)
    else:
        if data.status_code in (404, 500):
            context = {
                'error': data.error_message,
                'status_code': data.status_code,
                'current_user': data.current_user_dto
            }
            return templates.TemplateResponse(
                request=request,
                name='errors/error_page.html',
                context=context,
                status_code=data.status_code
            )
        else:
            error_msg = data['error_message']
            encoded_error = quote(error_msg)
            url = request.url_for('view_card', card_id=main_card_id)
            full_url = f'{url}?error={encoded_error}'
            return RedirectResponse(full_url, status_code=303)


@router.get(path='/card-{card_id}/upgrade_menu', name='view_upgrade_card')
async def view_upgrade_card(request: Request,
                            card_id: int,
                            session_db: AsyncSession = Depends(get_db_session),
                            current_user: User | None = Depends(get_current_user_with_profile),
                            error: str = None,
                            success: str = None
                            ):
    """ Просмотр меню усиления карты """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewUpgradeUseCase(session_db)
    data: ViewUpgradeUseCaseDict = await use_case.execute(current_card_id=card_id,
                                                          current_user=current_user)
    if data.get('upgrade_dto') is not None:
        context = {'request': request,
                   'current_user': current_user_dto,
                   'upgrade_dto': data.get('upgrade_dto'),
                   'error_message': error,
                   'success_message': success
                   }
        return templates.TemplateResponse(request=request,
                                          name='cards/upgrade_menu.html',
                                          context=context,
                                          status_code=data.get('status_code'))
    else:
        if data.get('status_code') in (400, 404, 500):
            context = {'error': data.get('error_message'),
                       'error_code': data.get('status_code')}
            return templates.TemplateResponse(request=request,
                                              name='errors/error_page.html',
                                              context=context,
                                              status_code=data.get('status_code')
                                              )


@router.post(path='/card-{card_id}/upgrade-{upgrade_id}', name='upgrade_card')
async def upgrade_card(request: Request,
                       card_id: int,
                       upgrade_id: int,
                       session_db: AsyncSession = Depends(get_db_session),
                       current_user_id: int | None = Depends(get_current_user_id)):
    """ Обработка запроса на повышение уровня карты """

    use_case = UpgradeUseCase(session_db=session_db)
    data: UpgradeUseCaseDict = await use_case.execute(current_user_id=current_user_id,
                                                      current_card_id=card_id,
                                                      upgrade_item_id=upgrade_id
                                                      )
    if data.get('success') is True:
        success_msg = data.get('success_message')
        encoded_success = quote(success_msg)
        url = request.url_for('view_upgrade_card', card_id=card_id)
        full_url = f'{url}?success={encoded_success}'
        return RedirectResponse(full_url, status_code=data.get('status_code'))
    else:
        if data.get('status_code') in (404, 500):
            context = {'error': data.get('error_message'),
                       'status_code': data.get('status_code'),
                       'current_user': data.get('current_user_dto')}
            return templates.TemplateResponse(request=request,
                                              name='errors/error_page.html',
                                              context=context,
                                              status_code=data.get('status_code')
                                              )
        else:
            error_msg = data['error_message']
            encoded_error = quote(error_msg)
            url = request.url_for('view_upgrade_card', card_id=card_id)
            full_url = f'{url}?error={encoded_error}'
            return RedirectResponse(full_url, status_code=303)
