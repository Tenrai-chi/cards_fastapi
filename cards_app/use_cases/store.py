import logging

from sqlalchemy.ext.asyncio import AsyncSession
from cards_app.exeptions import (
    InsufficientFundsUserError, NotEnoughSlotsError, CardNotOnSaleError,
    CardInStoreNotFoundError, BoxNotFoundError, ExpItemNotFoundError, AmuletNotFoundError,
    AmuletNotOnSaleError
)
from cards_app.schemas.base import ExpItemsBase
from cards_app.schemas.response import ViewCardStoreUseCaseResponse, ViewItemStoreUseCaseResponse, \
    BuyStoreCardUseCaseResponse, BuyBoxUseCaseResponse, BuyItemUseCaseResponse
from cards_app.schemas.store import (
    CardInStoreDTO, CardStoreDTO, BoxStoreDTO, AmuletsStoreDTO,
    UpgradeItemsStoreDTO, ExpItemsStoreDTO, AllStoreDTO, AmuletRewardDTO
)
from cards_app.services.cards import (
    get_temp_card_in_store, create_new_card_from_template,
    create_record_in_history_receiving_card
)
from cards_app.services.profile import check_can_user_receive_card, charge_user_gold, create_transaction
from cards_app.services.store import (
    get_cards_in_store, get_box_in_store, get_amulets_in_store,
    get_upgrade_items_in_store, get_exp_items_in_store, get_box_info, open_box_card,
    open_box_exp_item, open_box_amulet, buy_exp_items, buy_amulet, buy_upgrade_item
)
from cards_app.services.users import get_profile_for_update, get_user_with_profile, user_info_to_dto
from cards_app.utils.common import calculate_final_price
from cards_app.utils.response_types import ResponseType

logger = logging.getLogger(__name__)


class ViewCardStoreUseCase:
    """
    Use case для просмотра магазина карт.
    Преобразует данные для вывода информации о продаваемых картах.
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self) -> ViewCardStoreUseCaseResponse:
        """
        Выполняет получение списка карт, доступных в магазине, и формирует DTO.
        Returns:
            ViewCardStoreUseCaseResponse:
                - response_type (str): статус ответа.
                - card_store (CardStoreDTO | None): DTO со списком карт в магазине.
        Note:
            - SUCCESS: успешное получение данных.
            - SERVER_ERROR: непредвиденная ошибка.
        """

        try:
            all_cards: list = await get_cards_in_store(session_db=self.session_db)
            cards_in_store = []
            for card in all_cards:
                cards_in_store.append(
                    CardInStoreDTO(
                        id=card.id,
                        class_card_name=card.class_card.name,
                        rarity_card_name=card.rarity_card.name,
                        type_card_name=card.type_card.name,
                        class_card_pic=card.class_card.image,
                        hp=card.hp,
                        damage=card.damage,
                        price=card.price,
                        discount=card.discount,
                        discount_now=card.discount_now
                    )
                )
            card_store_dto = CardStoreDTO(cards=cards_in_store)
            return ViewCardStoreUseCaseResponse(
                response_type=ResponseType.SUCCESS,
                card_store=card_store_dto
            )

        except Exception as error:
            logger.error(f'Непредвиденная ошибка в ViewCardStoreUseCase: {error}', exc_info=True)
            return ViewCardStoreUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                card_store=None
            )


class BuyStoreCardUseCase:
    """ Use case для покупки карты в магазине """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            current_user_id: int | None,
            temp_card_id: int,
    ) -> BuyStoreCardUseCaseResponse:
        """
        Выполняет покупку карты в магазине.
        Args:
           current_user_id: ID User текущего пользователя
           temp_card_id: ID карты-шаблона в магазине

        Returns:
           BuyStoreCardUseCaseResponse:
               - error_message (str | None): сообщение об ошибке.
               - success_message (str | None): сообщение об успехе.
               - new_card_id (int | None): ID созданной карты (при успехе).
               - response_type (str): статус ответа.
        Note:
            - REDIRECT_WITH_INFO: успешное получение данных.
            - UNAUTHORIZED: неавторизованный пользователь.
            - REDIRECT_WITH_ERROR: неверный фильтр.
            - SERVER_ERROR: любая другая непредвиденная ошибка.
           """

        if current_user_id is None:
            logger.warning(f'Попытка неавторизованного пользователя купить карту в магазине')
            return BuyStoreCardUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                new_card_id=None,
                success_message=None,
                error_message=f'Для покупки карты вы должны быть авторизованы'
            )

        await get_profile_for_update(session_db=self.session_db, user_id=current_user_id)
        current_user = await get_user_with_profile(session_db=self.session_db, user_id=current_user_id)

        if current_user is None:
            logger.warning(f'Попытка неавторизованного пользователя купить карту в магазине')
            return BuyStoreCardUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                new_card_id=None,
                success_message=None,
                error_message=f'Для покупки карты вы должны быть авторизованы'
            )
        try:
            # Проверка, что у пользователя хватает места
            await check_can_user_receive_card(
                session_db=self.session_db,
                current_user=current_user,
                need_slots=1
            )

            # Взятие карты из магазина
            card_temp = await get_temp_card_in_store(session_db=self.session_db, card_temp_id=temp_card_id)
            if card_temp.discount_now:
                final_price_card: int = calculate_final_price(price=card_temp.price, discount=card_temp.discount)
            else:
                final_price_card: int = card_temp.price

            # Снятие денег
            gold_transaction: dict = await charge_user_gold(
                session_db=self.session_db,
                current_user=current_user,
                need_gold=final_price_card
            )

            # Создание карты
            new_card_id: int = await create_new_card_from_template(
                session_db=self.session_db,
                owner_id=current_user.profile.id,
                card_temp=card_temp
            )

            # Создание транзакции
            await create_transaction(
                session_db=self.session_db,
                user_profile_id=current_user.id,
                gold_before=gold_transaction['gold_before'],
                gold_after=gold_transaction['gold_after'],
                comment='Покупка в магазине карт'
            )

            # Создание записи о получении карты
            await create_record_in_history_receiving_card(
                session_db=self.session_db,
                card_id=new_card_id,
                user_profile_id=current_user.profile.id,
                method_receiving='Покупка в магазине'
            )
            await self.session_db.commit()
            return BuyStoreCardUseCaseResponse(
                response_type=ResponseType.REDIRECT_WITH_INFO,
                new_card_id=new_card_id,
                success_message=f'Вы успешно купили карту!',
                error_message=None
            )

        except (NotEnoughSlotsError, InsufficientFundsUserError, CardNotOnSaleError, CardInStoreNotFoundError) as error:
            await self.session_db.rollback()
            return BuyStoreCardUseCaseResponse(
                response_type=error.response_type,
                new_card_id=None,
                success_message=None,
                error_message=str(error)
            )

        except Exception as error:
            await self.session_db.rollback()
            logger.error(f'Непредвиденная ошибка в BuyStoreCardUseCase: {error}', exc_info=True)
            return BuyStoreCardUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                new_card_id=None,
                success_message=None,
                error_message=None
            )


class ViewItemStoreUseCase:
    """
    Use case для просмотра магазина предметов.
    Преобразует данные для вывода ассортимента магазина в зависимости от фильтра
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, store_filter: str) -> ViewItemStoreUseCaseResponse:
        """
        Выполняет получение списков предметов, доступных в магазине, и формирует DTO.
        Args:
           store_filter: фильтр магазина
        Returns:
            ViewItemStoreUseCaseResponse:
                - response_type (str): статус ответа.
                - store (ItemStoreDTO | None): DTO  ассортиментов магазина
        Note:
            - SUCCESS: успешное получение данных.
            - BAD_REQUEST: неправильный параметр фильтра.
            - SERVER_ERROR: непредвиденная ошибка
        """

        try:
            if store_filter == 'box':
                store_dto = AllStoreDTO(
                    boxes=await self._get_boxes_dto(),
                    exp_items=None,
                    amulets=None,
                    upgrade_items=None
                )

            elif store_filter == 'amulet':
                store_dto = AllStoreDTO(
                    boxes=None,
                    exp_items=None,
                    amulets=await self._get_amulets_dto(),
                    upgrade_items=None
                )

            elif store_filter == 'upgrade_item':
                store_dto = AllStoreDTO(
                    boxes=None,
                    exp_items=None,
                    amulets=None,
                    upgrade_items=await self._get_upgrade_items_dto()
                )

            elif store_filter == 'exp_items':
                store_dto = AllStoreDTO(
                    boxes=None,
                    exp_items=await self._get_exp_items_dto(),
                    amulets=None,
                    upgrade_items=None
                )

            elif store_filter == 'all':
                box = await self._get_boxes_dto()
                exp = await self._get_exp_items_dto()
                amu = await self._get_amulets_dto()
                upg = await self._get_upgrade_items_dto()
                store_dto = AllStoreDTO(
                    boxes=box,
                    exp_items=exp,
                    amulets=amu,
                    upgrade_items=upg
                )
            else:
                return ViewItemStoreUseCaseResponse(
                    response_type=ResponseType.BAD_REQUEST,
                    error_message=f'Неверный фильтр магазина',
                    store=None
                )

            return ViewItemStoreUseCaseResponse(
                response_type=ResponseType.SUCCESS,
                error_message=None,
                store=store_dto
            )
        except Exception as error:
            logger.error(f'Непредвиденная ошибка в ViewItemStoreUseCase: {error}', exc_info=True)
            return ViewItemStoreUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                store=None
            )

    async def _get_boxes_dto(self) -> list[BoxStoreDTO]:
        """ Преобразует DTO для сундуков """

        boxes: list = await get_box_in_store(session_db=self.session_db)
        boxes_dto = [
            BoxStoreDTO(
                id=box.id,
                name=box.name,
                description=box.description,
                price=box.price,
                image=box.image
            )
            for box in boxes
        ]
        return boxes_dto

    async def _get_amulets_dto(self) -> list[AmuletsStoreDTO]:
        """ Преобразует DTO для амулетов """

        amulets: list = await get_amulets_in_store(session_db=self.session_db)
        amulets_dto = [
            AmuletsStoreDTO(
                id=amulet.id,
                name=amulet.name,
                bonus_hp=amulet.bonus_hp,
                bonus_damage=amulet.bonus_damage,
                price=amulet.price,
                image=amulet.image,
                discount=amulet.discount,
                discount_now=amulet.discount_now,
                rarity_name=amulet.rarity.name,
            )
            for amulet in amulets
        ]
        return amulets_dto

    async def _get_upgrade_items_dto(self) -> list[UpgradeItemsStoreDTO]:
        """ Преобразует DTO для предметов усиления """

        upgrade_items: list = await get_upgrade_items_in_store(session_db=self.session_db)
        upgrade_items_dto = [
            UpgradeItemsStoreDTO(
                id=item.id,
                name=item.name,
                description=item.description,
                image=item.image,
                price=item.price,
            )
            for item in upgrade_items
        ]
        return upgrade_items_dto

    async def _get_exp_items_dto(self) -> list[ExpItemsStoreDTO]:
        """ Преобразует DTO для книг опыта """

        exp_items: list = await get_exp_items_in_store(session_db=self.session_db)
        exp_items_dto = [
            ExpItemsStoreDTO(
                id=item.id,
                name=item.name,
                experience_amount=item.experience_amount,
                price=item.price,
                image=item.image,
                sale_now=item.sale_now, )
            for item in exp_items
        ]
        return exp_items_dto


class BuyBoxUseCase:
    """ Use case для покупки сундука в магазине """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user_id: int | None, box_id: int) -> BuyBoxUseCaseResponse:
        """
        Выполняет открытие сундука.
        Args:
           current_user_id: ID User текущего пользователя
           box_id: ID сундука из магазина
        Returns:
            BuyBoxUseCaseResponse:
                - response_type (str): статус ответа.
                - exp_items_dto (list[ExpItemsBase] | None): предметы опыта.
                - amulets_items_dto (list[AmuletRewardDTO] | None): амулеты.
                - card_id: (int | None): ID полученной карты.
                - error_message: сообщение об ошибке.
                - success_message: сообщение об успехе.
                - current_user_dto: DTO текущего пользователя для перенаправления.
        Note:
            - REDIRECT_WITH_INFO: успешное открытие сундука.
            - REDIRECT_WITH_ERROR: какая-то ошибка, например нехватка золота или места в инвентаре.
            - UNAUTHORIZED: пользователь не авторизован.
            - NOT FOUND: не найден сундук.
            - SERVER_ERROR: любая непредвиденная ошибка
        """

        if current_user_id is None:
            logger.warning(f'Попытка неавторизованного пользователя купить сундук в магазине предметов')
            return BuyBoxUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для покупки сундука вы должны быть авторизованы',
                success_message=None,
                current_user=None,
                exp_items_dto=None,
                amulets_items_dto=None,
                card_id=None
            )

        await get_profile_for_update(session_db=self.session_db, user_id=current_user_id)
        current_user = await get_user_with_profile(session_db=self.session_db, user_id=current_user_id)

        if current_user is None:
            logger.warning(f'Попытка неавторизованного пользователя купить сундук в магазине предметов')
            return BuyBoxUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для покупки сундука вы должны быть авторизованы',
                success_message=None,
                current_user=None,
                exp_items_dto=None,
                amulets_items_dto=None,
                card_id=None
            )

        else:
            current_user_dto = await user_info_to_dto(user=current_user)

        try:
            box_info = await get_box_info(session_db=self.session_db, box_id=box_id)
            gold_transaction: dict = await charge_user_gold(
                session_db=self.session_db,
                current_user=current_user,
                need_gold=box_info.price
            )
            await create_transaction(
                session_db=self.session_db,
                user_profile_id=current_user.profile.id,
                gold_before=gold_transaction['gold_before'],
                gold_after=gold_transaction['gold_after'],
                comment='Покупка сундука'
            )

            if box_info.reward_type == 'card':
                new_card_id: int = await open_box_card(session_db=self.session_db, user=current_user)
                await create_record_in_history_receiving_card(
                    session_db=self.session_db,
                    card_id=new_card_id,
                    user_profile_id=current_user.profile.id,
                    method_receiving=f'Открытие сундука'
                )
                await self.session_db.commit()
                return BuyBoxUseCaseResponse(
                    response_type=ResponseType.REDIRECT_WITH_INFO,
                    error_message=None,
                    success_message=f'Вы получили карту из сундука!',
                    current_user=None,
                    exp_items_dto=None,
                    amulets_items_dto=None,
                    card_id=new_card_id
                )

            elif box_info.reward_type == 'exp_item':
                exp_items: list = await open_box_exp_item(session_db=self.session_db, user=current_user)
                exp_items_dto = [
                    ExpItemsBase(
                        name=item.name,
                        experience_amount=item.experience_amount,
                        image=item.image,
                    )
                    for item in exp_items
                ]
                await self.session_db.commit()
                return BuyBoxUseCaseResponse(
                    response_type=ResponseType.REDIRECT_WITH_INFO,
                    error_message=None,
                    success_message=f'Вы успешно открыли сундук с книгами опыта!',
                    current_user=current_user_dto,
                    exp_items_dto=exp_items_dto,
                    amulets_items_dto=None,
                    card_id=None
                )

            elif box_info.reward_type == 'amulet':
                amulets: list = await open_box_amulet(session_db=self.session_db, user=current_user)
                amulets_items_dto = [
                    AmuletRewardDTO(
                        id=amulet.id,
                        name=amulet.name,
                        bonus_hp=amulet.bonus_hp,
                        bonus_damage=amulet.bonus_damage,
                        image=amulet.image,
                        rarity_name=amulet.rarity.name
                    )
                    for amulet in amulets
                ]

                await self.session_db.commit()
                return BuyBoxUseCaseResponse(
                    response_type=ResponseType.REDIRECT_WITH_INFO,
                    error_message=None,
                    success_message=f'Вы успешно открыли сундук с амулетами!',
                    current_user=current_user_dto,
                    exp_items_dto=None,
                    amulets_items_dto=amulets_items_dto,
                    card_id=None
                )
            else:
                return BuyBoxUseCaseResponse(
                    response_type=ResponseType.SERVER_ERROR,
                    error_message=None,
                    success_message=None,
                    current_user=current_user_dto,
                    exp_items_dto=None,
                    amulets_items_dto=None,
                    card_id=None
                )

        except (BoxNotFoundError, InsufficientFundsUserError, NotEnoughSlotsError) as error:
            await self.session_db.rollback()
            return BuyBoxUseCaseResponse(
                response_type=error.response_type,
                error_message=str(error),
                success_message=None,
                current_user=current_user_dto,
                exp_items_dto=None,
                amulets_items_dto=None,
                card_id=None
            )

        except Exception as error:
            await self.session_db.rollback()
            logger.error(f'Непредвиденная ошибка в BuyBoxUseCase: {error}', exc_info=True)

            return BuyBoxUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                success_message=None,
                current_user=None,
                exp_items_dto=None,
                amulets_items_dto=None,
                card_id=None
            )


class BuyExpItemUseCase:
    """ Use case для покупки книг опыта в магазине """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            current_user_id: int | None,
            exp_item_id: int,
            amount: int
    ) -> BuyItemUseCaseResponse:
        """
        Выполняет покупку N количества книг.
        Args:
           current_user_id: ID User текущего пользователя
           exp_item_id: ID книги опыта
           amount: количество книг
        Returns:
            BuyItemUseCaseResponse:
                - response_type (str): статус ответа.
                - success_message (str | None):
                - error_message (str | None): сообщение об ошибке
        Note:
            - REDIRECT_WITH_INFO: успешное получение данных.
            - REDIRECT_WITH_ERROR: перенаправление с ошибкой.
            - UNAUTHORIZED: неавторизованный пользователь.
            - NOT_FOUND: не найдена книга.
            - SERVER_ERROR: непредвиденная ошибка.
        """

        if current_user_id is None:
            logger.warning(f'Попытка неавторизованного пользователя купить книгу опыта')
            return BuyItemUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для покупки книг опыта вы должны быть авторизованы',
                success_message=None
            )

        await get_profile_for_update(session_db=self.session_db, user_id=current_user_id)
        current_user = await get_user_with_profile(session_db=self.session_db, user_id=current_user_id)

        if current_user is None:
            logger.warning(f'Попытка неавторизованного пользователя получить бесплатную карту')
            return BuyItemUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для покупки книг опыта вы должны быть авторизованы',
                success_message=None
            )

        try:
            need_gold: int = await buy_exp_items(
                session_db=self.session_db,
                exp_item_id=exp_item_id,
                exp_item_amount=amount,
                user=current_user
            )
            gold_transaction: dict = await charge_user_gold(
                session_db=self.session_db,
                current_user=current_user,
                need_gold=need_gold
            )
            await create_transaction(
                session_db=self.session_db,
                user_profile_id=current_user.profile.id,
                gold_before=gold_transaction['gold_before'],
                gold_after=gold_transaction['gold_after'],
                comment=f'Покупка книг опыта в магазине'
            )

            await self.session_db.commit()
            return BuyItemUseCaseResponse(
                response_type=ResponseType.REDIRECT_WITH_INFO,
                error_message=None,
                success_message=f'Вы успешно купили {amount} книг'
            )

        except (InsufficientFundsUserError, ExpItemNotFoundError,) as error:
            await self.session_db.rollback()
            return BuyItemUseCaseResponse(
                response_type=error.response_type,
                error_message=str(error),
                success_message=None
            )

        except Exception as error:
            await self.session_db.rollback()
            logger.error(f'Непредвиденная ошибка в BuyExpItemUseCase: {error}', exc_info=True)
            return BuyItemUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                success_message=None
            )


class BuyAmuletUseCase:
    """ Use case для покупки амулета в магазине """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            current_user_id: int | None,
            amulet_id: int,
    ) -> BuyItemUseCaseResponse:
        """
        Выполняет покупку амулета в магазине.
        Args:
           current_user_id: ID User текущего пользователя
           amulet_id: ID амулета
        Returns:
            BuyItemUseCaseResponse:
                - response_type (str): статус ответа.
                - success_message (str | None):
                - error_message (str | None): сообщение об ошибке
        Note:
           - REDIRECT_WITH_INFO: успешное получение данных и перенаправление.
           - REDIRECT_WITH_ERROR: перенаправление с ошибкой.
           - UNAUTHORIZED: неавторизованный пользователь.
           - SERVER_ERROR: любая другая непредвиденная ошибка.
        """

        if current_user_id is None:
            logger.warning(f'Попытка неавторизованного пользователя купить амулет')
            return BuyItemUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=None,
                success_message=None
            )

        await get_profile_for_update(session_db=self.session_db, user_id=current_user_id)
        current_user = await get_user_with_profile(session_db=self.session_db, user_id=current_user_id)

        if current_user is None:
            logger.warning(f'Попытка неавторизованного пользователя купить амулет')
            return BuyItemUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=None,
                success_message=None
            )

        try:
            amulet_price: int = await buy_amulet(
                session_db=self.session_db,
                amulet_id=amulet_id,
                user=current_user
            )
            gold_transaction: dict = await charge_user_gold(
                session_db=self.session_db,
                current_user=current_user,
                need_gold=amulet_price
            )
            await create_transaction(
                session_db=self.session_db,
                user_profile_id=current_user.profile.id,
                gold_before=gold_transaction['gold_before'],
                gold_after=gold_transaction['gold_after'],
                comment=f'Покупка книг опыта в магазине'
            )

            await self.session_db.commit()
            return BuyItemUseCaseResponse(
                response_type=ResponseType.REDIRECT_WITH_INFO,
                error_message=None,
                success_message=f'Вы успешно купили амулет'
            )

        except (AmuletNotFoundError, AmuletNotOnSaleError, NotEnoughSlotsError,
                InsufficientFundsUserError, ) as error:
            await self.session_db.rollback()
            return BuyItemUseCaseResponse(
                response_type=error.response_type,
                error_message=str(error),
                success_message=None
            )

        except Exception as error:
            await self.session_db.rollback()
            logger.error(f'Непредвиденная ошибка в BuyAmuletUseCase: {error}', exc_info=True)
            return BuyItemUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                success_message=None
            )


class BuyUpgradeItemUseCase:
    """ Use case для покупки предмета усиления в магазине """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            current_user_id: int | None,
            upgrade_item_id: int,
    ) -> BuyItemUseCaseResponse:
        """
        Выполняет покупку предмета усиления в магазине.
        Args:
           current_user_id: ID User текущего пользователя
           upgrade_item_id: ID предмета усиления
        Returns:
            BuyItemUseCaseDict:
                - response_type (str): статус ответа.
                - success_message (str | None):
                - error_message (str | None): сообщение об ошибке
        Note:
            - REDIRECT_WITH_INFO: успешное получение данных и перенаправление.
            - REDIRECT_WITH_ERROR: перенаправление с ошибкой.
            - UNAUTHORIZED: неавторизованный пользователь.
            - SERVER_ERROR: любая другая непредвиденная ошибка.
        """

        if current_user_id is None:
            logger.warning(f'Попытка неавторизованного пользователя купить амулет')
            return BuyItemUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=None,
                success_message=None
            )

        await get_profile_for_update(session_db=self.session_db, user_id=current_user_id)
        current_user = await get_user_with_profile(session_db=self.session_db, user_id=current_user_id)

        if current_user is None:
            logger.warning(f'Попытка неавторизованного пользователя купить амулет')
            return BuyItemUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=None,
                success_message=None
            )

        try:
            need_gold: int = await buy_upgrade_item(
                session_db=self.session_db,
                upgrade_item_id=upgrade_item_id,
                user=current_user
            )
            gold_transaction: dict = await charge_user_gold(
                session_db=self.session_db,
                current_user=current_user,
                need_gold=need_gold
            )
            await create_transaction(
                session_db=self.session_db,
                user_profile_id=current_user.profile.id,
                gold_before=gold_transaction['gold_before'],
                gold_after=gold_transaction['gold_after'],
                comment=f'Покупка книг опыта в магазине'
            )

            await self.session_db.commit()
            return BuyItemUseCaseResponse(
                response_type=ResponseType.REDIRECT_WITH_INFO,
                error_message=None,
                success_message=f'Вы успешно купили предмет усиления'
            )

        except (InsufficientFundsUserError, ExpItemNotFoundError,) as error:
            await self.session_db.rollback()
            return BuyItemUseCaseResponse(
                response_type=error.response_type,
                error_message=str(error),
                success_message=None
            )

        except Exception as error:
            await self.session_db.rollback()
            logger.error(f'Непредвиденная ошибка в BuyUpgradeItemUseCase: {error}', exc_info=True)
            return BuyItemUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                success_message=None
            )
