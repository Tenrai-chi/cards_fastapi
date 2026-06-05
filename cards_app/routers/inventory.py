from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse
from urllib.parse import quote

from cards_app.auth.dependencies import get_current_user_with_profile
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.services.users import user_info_to_dto
from cards_app.models.users import User
from cards_app.types import ViewInventoryUseCaseDict, SaleAmuletUseCaseDict
from cards_app.use_cases.inventory import ViewInventoryUseCase, SaleAmuletUseCase

router = APIRouter(prefix='/inventory', tags=['inventory'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get(path='/{inventory_filter}', name='inventory')
async def inventory(request: Request,
                    session_db: AsyncSession = Depends(get_db_session),
                    current_user: User | None = Depends(get_current_user_with_profile),
                    inventory_filter: str = 'all',
                    error: str = None,
                    success: str = None
                    ):
    """ Просмотр инвентаря пользователя """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewInventoryUseCase(session_db)
    data: ViewInventoryUseCaseDict = await use_case.execute(current_user=current_user,
                                                            inventory_filter=inventory_filter)
    if data.get('inventory_dto'):
        context = {'request': request,
                   'current_user': current_user_dto,
                   'inventory_dto': data.get('inventory_dto'),
                   'error_message': error,
                   'success_message': success,
                   'current_inventory_filter': inventory_filter
                   }

        return templates.TemplateResponse(request=request,
                                          name='inventory/inventory.html',
                                          context=context,
                                          status_code=data.get('status_code'))
    else:
        return templates.TemplateResponse(request=request,
                                          name='errors/error_page.html',
                                          context={'error': data.get('error_message'),
                                                   'status_code': data.get('status_code'),
                                                   'current_user': current_user_dto},
                                          status_code=data.get('status_code')
                                          )


# @router.get(path='/level_up/{card_id}', name='view_level_up')
# async def view_level_up(request: Request,
#                         card_id: int,
#                         session_db: AsyncSession = Depends(get_db_session),
#                         current_user: User | None = Depends(get_current_user_with_profile),
#                         error: str = None,
#                         success: str = None
#                         ):
#     """ Просмотр страницы для улучшения карты """
    # todo сделать позже
    # pass
    # current_user_dto = await user_info_to_dto(current_user)
    # use_case = ViewInventoryUseCase(session_db)
    # data: ViewInventoryUseCaseDict = await use_case.execute(current_user=current_user,
    #                                                         inventory_filter=inventory_filter)
    # if data.get('inventory_dto'):
    #     context = {'request': request,
    #                'current_user': current_user_dto,
    #                'inventory_dto': data.get('inventory_dto'),
    #                'error_message': error,
    #                'success_message': success,
    #                'current_inventory_filter': inventory_filter
    #                }
    #
    #     return templates.TemplateResponse(request=request,
    #                                       name='inventory/inventory.html',
    #                                       context=context,
    #                                       status_code=data.get('status_code'))
    # else:
    #     return templates.TemplateResponse(request=request,
    #                                       name='errors/error_page.html',
    #                                       context={'error': data.get('error_message'),
    #                                                'status_code': data.get('status_code'),
    #                                                'current_user': current_user_dto},
    #                                       status_code=data.get('status_code')
    #                                       )


@router.post(path='/sell_amulet/{amulet_id}', name='sell_amulet')
async def sell_amulet(request: Request,
                      amulet_id: int,
                      session_db: AsyncSession = Depends(get_db_session),
                      current_user: User | None = Depends(get_current_user_with_profile),
                      ):
    """ Продажа амулета """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = SaleAmuletUseCase(session_db)
    data: SaleAmuletUseCaseDict = await use_case.execute(current_user, amulet_id=amulet_id)
    if data.get('success'):
        success_msg = data.get('success_message')
        encoded_success = quote(success_msg)
        url = request.url_for('inventory', inventory_filter='amulets')
        full_url = f'{url}?success={encoded_success}'
        return RedirectResponse(full_url, status_code=data.get('status_code'))

    elif data.get('status_code') == 400:
        error_msg = data['error_message']
        encoded_error = quote(error_msg)
        url = request.url_for('inventory', inventory_filter='amulets')
        full_url = f'{url}?error={encoded_error}'
        return RedirectResponse(full_url, status_code=303)

    elif data.get('status_code') in (404, 500):
        return templates.TemplateResponse(request=request,
                                          name='errors/error_page.html',
                                          context={'error': data.get('error_message'),
                                                   'status_code': data.get('status_code'),
                                                   'current_user': current_user_dto},
                                          status_code=data.get('status_code')
                                          )
