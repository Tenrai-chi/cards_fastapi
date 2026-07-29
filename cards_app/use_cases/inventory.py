import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.exeptions import InventoryException
from cards_app.models import User
from cards_app.schemas.inventory import (
    ExpItemsInventoryDTO, AmuletsInventoryDTO,
    UpgradeItemsInventoryDTO, FullInventoryDTO
)
from cards_app.schemas.response import ViewInventoryUseCaseResponse, SaleAmuletUseCaseResponse
from cards_app.services.inventory import (
    get_amulets_in_user_inventory, get_upgrade_items_in_user_inventory,
    get_exp_items_in_user_inventory, delete_amulet
)
from cards_app.services.profile import add_user_gold, create_transaction
from cards_app.services.users import get_profile_for_update, get_user_with_profile
from cards_app.utils.response_types import ResponseType

logger = logging.getLogger(__name__)


class ViewInventoryUseCase:
    """ Use case для просмотра инвентаря пользователя """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user: User | None, inventory_filter: str
                      ) -> ViewInventoryUseCaseResponse:
        """
        Выполняет получение инвентаря пользователя с примененным фильтром.
        Args:
           current_user: User + Profile текущего пользователя
           inventory_filter: фильтр инвентаря
        Returns:
           ViewInventoryUseCaseResponse:
               - inventory(InventoryDTO | None): DTO избранных пользователей
               - response_type (str): статус ответа.
               - error_message: текст ошибки
        Note:
            - SUCCESS: успешное получение данных.
            - UNAUTHORIZED: неавторизованный пользователь.
            - BAD_REQUEST: неверный фильтр.
            - SERVER_ERROR: любая другая непредвиденная ошибка.
       """

        if current_user is None:
            logger.warning(f'Попытка неавторизованного пользователя просмотреть инвентарь')
            return ViewInventoryUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для просмотра инвентаря необходимо быть авторизованным',
                inventory=None
            )

        try:
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
                exp_items = await self._get_exp_items_dto(owner_id=current_user.profile.id)
                amulets = await self._get_amulets_dto(owner_id=current_user.profile.id)
                upgrade_items = await self._get_upgrade_items_dto(owner_id=current_user.profile.id)
                inventory_dto = FullInventoryDTO(
                    exp_items=exp_items,
                    amulets=amulets,
                    upgrade_items=upgrade_items,
                    count_amulet=len(amulets),
                    max_count_amulets=current_user.profile.amulet_slots
                )

            else:
                return ViewInventoryUseCaseResponse(
                    response_type=ResponseType.BAD_REQUEST,
                    error_message=f'Неверный фильтр инвентаря',
                    inventory=None
                )

            return ViewInventoryUseCaseResponse(
                response_type=ResponseType.SUCCESS,
                error_message=None,
                inventory=inventory_dto
            )
        except Exception as error:
            logger.error(f'Непредвиденная ошибка в ViewInventoryUseCase: {error}', exc_info=True)
            return ViewInventoryUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                inventory=None
            )

    async def _get_exp_items_dto(self, owner_id: int) -> list[ExpItemsInventoryDTO]:
        """ Преобразует DTO для предметов опыта """

        exp_items: list = await get_exp_items_in_user_inventory(
            session_db=self.session_db,
            owner_id=owner_id
        )
        exp_items_dto = [
            ExpItemsInventoryDTO(
                name=item.item.name,
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

        amulets: list = await get_amulets_in_user_inventory(
            session_db=self.session_db,
            owner_id=owner_id
        )
        amulets_dto = [
            AmuletsInventoryDTO(
                card_id=amulet.card.id if amulet.card else None,
                card_class_name=amulet.card.class_card.name if amulet.card else None,
                card_rarity_name=amulet.card.rarity_card.name if amulet.card else None,
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

        upg_items: list = await get_upgrade_items_in_user_inventory(
            session_db=self.session_db,
            owner_id=owner_id
        )
        upg_items_dto = [
            UpgradeItemsInventoryDTO(
                id=item.id,
                name=item.upgrade_item_type.name,
                description=item.upgrade_item_type.description,
                image=item.upgrade_item_type.image,
                gold_for_use=item.upgrade_item_type.price_of_use,
                amount=item.amount
            )
            for item in upg_items
        ]
        return upg_items_dto


class SaleAmuletUseCase:
    """ Use case для продажи амулета """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user_id: int | None, amulet_id: int
                      ) -> SaleAmuletUseCaseResponse:
        """
        Выполняет запрос на продажу амулета из инвентаря пользователя.
        Args:
           current_user_id: ID User текущего пользователя.
           amulet_id: ID амулета.
        Returns:
           SaleAmuletUseCaseResponse:
               - response_type (str): статус ответа.
               - error_message: текст ошибки
               - success_message: сообщение об успехе
        Note:
           - REDIRECT_WITH_INFO: успешная продажа.
           - REDIRECT_WITH_ERROR: перенаправление с ошибкой.
           - UNAUTHORIZED: неавторизованный пользователь.
           - FORBIDDEN: не является владельцем.
           - NOT_FOUND: амулет не найден.
           - SERVER_ERROR: любая другая непредвиденная ошибка.
       """

        if current_user_id is None:
            logger.warning(f'Попытка неавторизованного пользователя продать амулет')
            return SaleAmuletUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для продажи амулета вы должны быть авторизованы',
                success_message=None
            )

        await get_profile_for_update(session_db=self.session_db, user_id=current_user_id)
        current_user = await get_user_with_profile(session_db=self.session_db, user_id=current_user_id)

        if current_user is None:
            logger.warning(f'Попытка неавторизованного пользователя продать амулет')
            return SaleAmuletUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для продажи амулета вы должны быть авторизованы',
                success_message=None
            )

        try:
            # Удаление амулета
            add_gold_for_sell: int = await delete_amulet(
                session_db=self.session_db,
                owner_id=current_user.profile.id,
                amulet_id=amulet_id
            )
            # Добавление золота
            gold_data: dict = await add_user_gold(
                session_db=self.session_db,
                current_user=current_user,
                add_gold=add_gold_for_sell
            )
            # Создание транзакции
            await create_transaction(
                session_db=self.session_db,
                user_profile_id=current_user.profile.id,
                gold_before=gold_data.get('gold_before'),
                gold_after=gold_data.get('gold_after'),
                comment=f'Продажа амулета'
            )

            await self.session_db.commit()
            return SaleAmuletUseCaseResponse(
                response_type=ResponseType.REDIRECT_WITH_INFO,
                error_message=None,
                success_message=f'Вы успешно продали амулет за {add_gold_for_sell} золота'
            )

        except InventoryException as error:
            await self.session_db.rollback()
            return SaleAmuletUseCaseResponse(
                response_type=error.response_type,
                error_message=str(error),
                success_message=None
            )

        except Exception as error:
            await self.session_db.rollback()
            logger.error(f'Непредвиденная ошибка в SaleAmuletUseCase: {error}', exc_info=True)
            return SaleAmuletUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                success_message=None
            )
