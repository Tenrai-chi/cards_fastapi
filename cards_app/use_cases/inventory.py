import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.exeptions import InventoryException
from cards_app.models import User
from cards_app.schemas import ExpItemsInventoryDTO, UpgradeItemsInventoryDTO, AmuletsInventoryDTO, FullInventoryDTO
from cards_app.services.inventory import (get_amulets_in_user_inventory, get_upgrade_items_in_user_inventory,
                                          get_exp_items_in_user_inventory, delete_amulet)
from cards_app.services.profile import add_user_gold, create_transaction
from cards_app.types import ViewInventoryUseCaseDict, SaleAmuletUseCaseDict

logger = logging.getLogger(__name__)


class ViewInventoryUseCase:
    """ Use case для просмотра инвентаря пользователя """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user: User | None, inventory_filter: str
                      ) -> ViewInventoryUseCaseDict:
        """ Формирует InventoryDTO пользователя
           Args:
               current_user: User + Profile текущего пользователя
               inventory_filter: фильтр инвентаря
           Returns:
               ViewInventoryUseCaseDict:
                   - inventory_dto (InventoryDTO | None): DTO избранных пользователей
                   - status_code (int): HTTP статус-код.
                   - error_message: текст ошибки
           Note:
               - 200: успешное получение данных
               - 400: если пользователь не авторизован
       """

        answer_data = {'inventory_dto': None,
                       'status_code': None,
                       'error_message': None}
        if current_user is None:
            answer_data['error_message'] = f'Для просмотра инвентаря необходимо быть авторизованным'
            answer_data['status_code'] = 400
            return answer_data

        if inventory_filter == 'exp_items':
            inventory_dto = FullInventoryDTO(
                exp_items=await self._get_exp_items_dto(owner_id=current_user.profile.id),
                amulets=None,
                upgrade_items=None,
            )

        elif inventory_filter == 'amulets':
            amulets_list = await self._get_amulets_dto(owner_id=current_user.profile.id)
            inventory_dto = FullInventoryDTO(
                exp_items=None,
                amulets=amulets_list,
                upgrade_items=None,
                count_amulet=len(amulets_list),
                max_count_amulets=current_user.profile.amulet_slots
            )

        elif inventory_filter == 'upgrade_items':
            inventory_dto = FullInventoryDTO(
                exp_items=None,
                amulets=None,
                upgrade_items=await self._get_upgrade_items_dto(owner_id=current_user.profile.id)
            )

        elif inventory_filter == 'all':

            exp, amu, upg = await asyncio.gather(self._get_exp_items_dto(owner_id=current_user.profile.id),
                                                 self._get_amulets_dto(owner_id=current_user.profile.id),
                                                 self._get_upgrade_items_dto(owner_id=current_user.profile.id),
                                                 )
            inventory_dto = FullInventoryDTO(exp_items=exp,
                                             amulets=amu,
                                             upgrade_items=upg,
                                             count_amulet=len(amu),
                                             max_count_amulets=current_user.profile.amulet_slots
                                             )

        else:
            answer_data['status_code'] = 500
            answer_data['error_message'] = f'Неверный фильтр инвентаря'
            return answer_data

        answer_data['inventory_dto'] = inventory_dto
        answer_data['status_code'] = 200
        return answer_data

    async def _get_exp_items_dto(self, owner_id: int) -> list[ExpItemsInventoryDTO]:
        """ Преобразует DTO для предметов опыта """

        exp_items: list = await get_exp_items_in_user_inventory(session_db=self.session_db,
                                                                owner_id=owner_id)
        exp_items_dto = [ExpItemsInventoryDTO(name=item.item.name,
                                              rarity=item.item.rarity,
                                              experience_amount=item.item.experience_amount,
                                              image=item.item.image,
                                              gold_for_use=item.item.gold_for_use,
                                              amount=item.amount
                                              )
                         for item in exp_items
                         ]
        return exp_items_dto

    async def _get_amulets_dto(self, owner_id: int) -> list[AmuletsInventoryDTO]:
        """ Преобразует DTO для амулетов """

        amulets: list = await get_amulets_in_user_inventory(session_db=self.session_db,
                                                            owner_id=owner_id)
        amulets_dto = [AmuletsInventoryDTO(card_id=amulet.card.id if amulet.card else None,
                                           card_class_name=(amulet.card.class_card.name
                                                            if amulet.card
                                                            else None),
                                           card_rarity_name=(amulet.card.rarity_card.name
                                                             if amulet.card
                                                             else None),
                                           id=amulet.id,
                                           name=amulet.amulet_type.name,
                                           rarity_name=amulet.amulet_type.rarity.name,
                                           bonus_hp=amulet.amulet_type.bonus_hp,
                                           bonus_damage=amulet.amulet_type.bonus_damage,
                                           image=amulet.amulet_type.image,
                                           price_for_sale=amulet.amulet_type.price // 2,
                                           upgrades=amulet.upgrades,
                                           max_upgrade=amulet.amulet_type.rarity.max_upgrade,
                                           )
                       for amulet in amulets
                       ]
        return amulets_dto

    async def _get_upgrade_items_dto(self, owner_id: int) -> list[UpgradeItemsInventoryDTO]:
        """ Преобразует DTO для предметов усиления """

        upg_items: list = await get_upgrade_items_in_user_inventory(session_db=self.session_db,
                                                                    owner_id=owner_id)
        upg_items_dto = [UpgradeItemsInventoryDTO(id=item.id,
                                                  name=item.upgrade_item_type.name,
                                                  description=item.upgrade_item_type.description,
                                                  image=item.upgrade_item_type.image,
                                                  gold_for_use=item.upgrade_item_type.price_of_use,
                                                  amount=item.amount)
                         for item in upg_items
                         ]
        return upg_items_dto


class SaleAmuletUseCase:
    """ Use case продажи амулета """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user: User | None, amulet_id: int
                      ) -> SaleAmuletUseCaseDict:
        """ Формирует InventoryDTO пользователя
           Args:
               current_user: User + Profile текущего пользователя
               amulet_id: ID амулета
           Returns:
               SaleAmuletUseCaseDict:
                   - success: успех или неудача
                   - status_code (int): HTTP статус-код.
                   - error_message: текст ошибки
                   - success_message: сообщение об успехе
           Note:
               - 303: успешная продажа
               - 400: если пользователь не авторизован или не является владельцем
               - 404: если амулет не найден
       """

        answer_data = {'success': None,
                       'status_code': None,
                       'error_message': None,
                       'success_message': None}

        if current_user is None:
            answer_data['error_message'] = f'Вы должны авторизоваться'
            answer_data['status_code'] = 400
            answer_data['success'] = False
            return answer_data

        try:
            # Удаление амулета
            add_gold_for_sell: int = await delete_amulet(session_db=self.session_db,
                                                         owner_id=current_user.profile.id,
                                                         amulet_id=amulet_id)
            # Добавление золота
            gold_data: dict = await add_user_gold(session_db=self.session_db,
                                                  current_user=current_user,
                                                  add_gold=add_gold_for_sell)
            # Создание транзакции
            await create_transaction(session_db=self.session_db,
                                     user_profile_id=current_user.profile.id,
                                     gold_before=gold_data.get('gold_before'),
                                     gold_after=gold_data.get('gold_after'),
                                     comment=f'Продажа амулета')

            await self.session_db.commit()
            answer_data['success'] = True
            answer_data['status_code'] = 303
            answer_data['success_message'] = f'Вы успешно продали амулет за {add_gold_for_sell} золота'

        except InventoryException as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в SaleAmuletUseCase: {error}', exc_info=True)
        return answer_data
