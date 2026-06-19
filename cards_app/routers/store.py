from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import quote

from cards_app.auth.dependencies import get_current_user_with_profile, get_current_user_id
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.services.users import user_info_to_dto
from cards_app.types import (ViewCardStoreUseCaseDict, ViewItemStoreUseCaseDict, BuyBoxUseCaseDict,
                             BuyItemUseCaseDict, BuyStoreCardUseCaseDict)
from cards_app.use_cases.store import (BuyStoreCardUseCase, ViewItemStoreUseCase, BuyBoxUseCase, BuyExpItemUseCase,
                                       BuyAmuletUseCase, BuyUpgradeItemUseCase)

from cards_app.models.users import User
from cards_app.use_cases.store import ViewCardStoreUseCase

router = APIRouter(prefix='/store', tags=['store'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get(path='/cards', name='card_store')
async def view_card_store(request: Request,
                          session_db: AsyncSession = Depends(get_db_session),
                          current_user: User | None = Depends(get_current_user_with_profile),
                          error: str = None
                          ):
    """ Просмотр страницы магазина карт """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewCardStoreUseCase(session_db)
    data: ViewCardStoreUseCaseDict = await use_case.execute()

    context = {'request': request,
               'current_user': current_user_dto,
               'card_store_dto': data.get('card_store_dto'),
               'error_message': error,
               }

    return templates.TemplateResponse(request=request,
                                      name='store/card_store.html',
                                      context=context,
                                      status_code=data.get('status_code'))


@router.get(path='/items/{store_filter}', name='item_store')
async def view_items_store(request: Request,
                           session_db: AsyncSession = Depends(get_db_session),
                           current_user: User | None = Depends(get_current_user_with_profile),
                           store_filter: str = 'all',
                           error: str = None
                           ):
    """ Просмотр страницы магазина карт """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = ViewItemStoreUseCase(session_db)
    data: ViewItemStoreUseCaseDict = await use_case.execute(store_filter=store_filter)
    if data.get('store_dto'):
        context = {'request': request,
                   'current_user': current_user_dto,
                   'store_dto': data.get('store_dto'),
                   'error_message': error,
                   'current_store_filter': store_filter
                   }
        return templates.TemplateResponse(request=request,
                                          name='store/item_store.html',
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


@router.post(path='/cards/buy-{card_id}', name='buy_card_in_store')
async def buy_card_in_store(request: Request,
                            session_db: AsyncSession = Depends(get_db_session),
                            current_user_id: int | None = Depends(get_current_user_id),
                            card_id: int = None
                            ):
    """ Покупка в магазине карт """

    use_case = BuyStoreCardUseCase(session_db)
    data: BuyStoreCardUseCaseDict = await use_case.execute(current_user_id=current_user_id,
                                                           temp_card_id=card_id)

    if data.get('success') is True:
        new_card_id = data.get('new_card_id')
        url = request.url_for('view_card', card_id=new_card_id)
        return RedirectResponse(url, status_code=data.get('status_code'))
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
            url = request.url_for('card_store')
            full_url = f'{url}?error={encoded_error}'
            return RedirectResponse(full_url, status_code=303)


@router.post(path='/open/box-{box_id}', name='buy_box_in_store')
async def buy_box_in_store(request: Request,
                           session_db: AsyncSession = Depends(get_db_session),
                           current_user_id: int | None = Depends(get_current_user_id),
                           box_id: int = None
                           ):
    """ Покупка сундука в магазина """

    use_case = BuyBoxUseCase(session_db)
    data: BuyBoxUseCaseDict = await use_case.execute(current_user_id=current_user_id,
                                                     box_id=box_id)

    if data.get('exp_items_dto'):
        context = {'request': request,
                   'current_user': data.get('current_user_dto'),
                   'exp_items_dto': data.get('exp_items_dto'),
                   }
        return templates.TemplateResponse(request=request,
                                          name='store/open_exp_items_box.html',
                                          context=context,
                                          status_code=data.get('status_code'))

    if data.get('amulets_items_dto'):
        context = {'request': request,
                   'current_user': data.get('current_user_dto'),
                   'amulets_items_dto': data.get('amulets_items_dto'),
                   }
        return templates.TemplateResponse(request=request,
                                          name='store/open_amulets_box.html',
                                          context=context,
                                          status_code=data.get('status_code'))

    if data.get('card_id'):
        new_card_id = data.get('card_id')
        url = request.url_for('view_card', card_id=new_card_id)
        return RedirectResponse(url, status_code=data.get('status_code'))
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
            url = request.url_for('card_store')
            full_url = f'{url}?error={encoded_error}'
            return RedirectResponse(full_url, status_code=303)


@router.post(path='/buy_book/book-{book_id}', name='buy_book_in_store')
async def buy_book_in_store(request: Request,
                            book_id: int,
                            amount: int = Form(...),
                            session_db: AsyncSession = Depends(get_db_session),
                            current_user_id: int | None = Depends(get_current_user_id),
                            ):
    """ Покупка книги в магазине """

    use_case = BuyExpItemUseCase(session_db)
    data: BuyItemUseCaseDict = await use_case.execute(current_user_id=current_user_id,
                                                      exp_item_id=book_id,
                                                      amount=amount,
                                                      )

    if data.get('success') is True:
        success_msg = data['success_message']
        encoded_success = quote(success_msg)
        url = request.url_for('item_store', store_filter='exp_items')
        full_url = f'{url}?success={encoded_success}'
        return RedirectResponse(full_url, status_code=303)
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
            url = request.url_for('item_store', store_filter='exp_items')
            full_url = f'{url}?error={encoded_error}'
            return RedirectResponse(full_url, status_code=303)


@router.post(path='/buy_amulet/amulet-{amulet_id}', name='buy_amulet_in_store')
async def buy_amulet_in_store(request: Request,
                              amulet_id: int,
                              session_db: AsyncSession = Depends(get_db_session),
                              current_user: User | None = Depends(get_current_user_with_profile),
                              ):
    """ Покупка амулета в магазине """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = BuyAmuletUseCase(session_db)
    data: BuyItemUseCaseDict = await use_case.execute(current_user=current_user,
                                                      amulet_id=amulet_id,
                                                      )

    if data.get('success') is True:
        success_msg = data['success_message']
        encoded_success = quote(success_msg)
        url = request.url_for('item_store', store_filter='amulet')
        full_url = f'{url}?success={encoded_success}'
        return RedirectResponse(full_url, status_code=303)
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
            url = request.url_for('item_store', store_filter='amulet')
            full_url = f'{url}?error={encoded_error}'
            return RedirectResponse(full_url, status_code=303)


@router.post(path='/buy_upgrade_item/upgrade_item-{upgrade_item_id}', name='buy_upgrade_item_in_store')
async def buy_upgrade_item_in_store(request: Request,
                                    upgrade_item_id: int,
                                    session_db: AsyncSession = Depends(get_db_session),
                                    current_user: User | None = Depends(get_current_user_with_profile),
                                    ):
    """ Покупка амулета в магазине """

    current_user_dto = await user_info_to_dto(current_user)
    use_case = BuyUpgradeItemUseCase(session_db)
    data: BuyItemUseCaseDict = await use_case.execute(current_user=current_user,
                                                      upgrade_item_id=upgrade_item_id,
                                                      )

    if data.get('success') is True:
        success_msg = data['success_message']
        encoded_success = quote(success_msg)
        url = request.url_for('item_store', store_filter='upgrade_item')
        full_url = f'{url}?success={encoded_success}'
        return RedirectResponse(full_url, status_code=303)
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
            url = request.url_for('item_store', store_filter='upgrade_item')
            full_url = f'{url}?error={encoded_error}'
            return RedirectResponse(full_url, status_code=303)
