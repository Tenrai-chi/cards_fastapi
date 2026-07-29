import logging
from cards_app.utils.response_types import ResponseType

from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.schemas.base import AmuletBase
from cards_app.schemas.inventory import FullInfoUpgradingDTO, CardUpgradingDTO, UpgradeItemsInventoryDTO
from cards_app.schemas.response import (
    ViewCardUseCaseResponse, ViewGetFreeCardUseCaseResponse,
    GetFreeCardUseCaseResponse, ViewUserCardsUseResponse, ViewTradingUseCaseResponse, ViewMergeUseCaseResponse,
    MergeUseCaseResponse, ViewUpgradeUseCaseResponse, UpgradeUseCaseResponse
)
from cards_app.services.inventory import get_upgrade_items_in_user_inventory
from cards_app.services.users import get_user_with_profile, user_info_to_dto, get_profile_for_update
from cards_app.exeptions import (
    NotEnoughSlotsError, CooldownNotElapsedError, CardNotFoundError, NotCardOwnerError,
    TooManyCardsMergeError, SelfMergeError, NotEnoughUpgradeItemsError,
    InsufficientFundsUserError, MaxUpgradeCardError, UserNotFoundError
)
from cards_app.services.cards import (
    get_card_with_details, get_rarities_and_classes, generate_random_card,
    create_record_in_history_receiving_card, get_all_cards_user, get_cards_in_trading,
    get_cards_for_merge, merge_card
)
from cards_app.services.inventory import upgrade_card
from cards_app.schemas.cards import (
    CardDTO, CardInfoDTO, GetFreeCardDTO, RarityCard, ClassCard, UserCardsDTO,
    CardsTradingDTO, OneCardForMergeDTO, CardsForMergeDTO
)

from cards_app.services.profile import (
    update_user_receiving_timer, check_can_user_receive_card, get_base_info_profile,
    charge_user_gold, create_transaction
)

from cards_app.utils.common import calculate_need_exp, time_difference_check
from cards_app.models.users import User

logger = logging.getLogger(__name__)


class ViewCardUseCase:
    """ Use case для просмотра информации о конкретной карте """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            card_id: int,
            current_user: User | None
    ) -> ViewCardUseCaseResponse:
        """
        Выполняет получение информации о карте и надетом амулете при наличии.
        Args:
           card_id: ID карты для просмотра.
           current_user: User + Profile текущего пользователя
        Returns:
           ViewCardUseCaseResponse:
               - card_info (CardDTO | None): DTO с данными карты, амулета и флагом владельца.
               - error_message (str | None): текст ошибки, если произошла.
               - response_type (str): статус ответа.
        Note:
           - SUCCESS: успешное получение данных.
           - NOT_FOUND: карта не найдена.
           - SERVER_ERROR: любая другая непредвиденная ошибка.
        """

        try:
            card = await get_card_with_details(session_db=self.session_db, card_id=card_id)

        except CardNotFoundError as error:
            return ViewCardUseCaseResponse(
                response_type=error.response_type,
                error_message=str(error),
                card_info=None
            )

        except Exception as error:
            logger.error(f'Непредвиденная ошибка в ViewCardUseCase: {error}', exc_info=True)
            return ViewCardUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                card_info=None
            )

        need_exp: int = calculate_need_exp(level=card.level)
        card_dto = CardDTO(
            id=card.id,
            class_card_name=card.class_card.name,
            rarity_card_name=card.rarity_card.name,
            type_card_name=card.type_card.name,
            class_card_pic=card.class_card.image,
            hp=card.hp,
            damage=card.damage,
            skill=card.class_card.skill,
            level=card.level,
            max_level=card.rarity_card.max_level,
            merger=card.merger,
            max_merger=card.max_merger,
            enhancement=card.enhancement,
            max_enhancement=card.max_enhancement,
            current_exp=card.experience_bar,
            need_exp=need_exp
        )

        amulet_dto = None
        if card.amulet:
            amulet_dto = AmuletBase(
                id=card.amulet.id,
                name=card.amulet.amulet_type.name,
                bonus_hp=card.amulet.amulet_type.bonus_hp,
                bonus_damage=card.amulet.amulet_type.bonus_damage,
            )

        if current_user:
            is_owner = True if current_user.profile.id == card.owner_id else False
        else:
            is_owner = False

        card_info = CardInfoDTO(
            card=card_dto,
            amulet=amulet_dto,
            is_owner=is_owner
        )

        return ViewCardUseCaseResponse(
            response_type=ResponseType.SUCCESS,
            card_info=card_info,
            error_message=None
        )


class ViewGetFreeCardUseCase:
    """ Use case для просмотра страницы с получением бесплатной карты. """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            current_user: User | None
    ) -> ViewGetFreeCardUseCaseResponse:
        """
        Получает списки всех классов, редкостей и флаг возможности получить карту сейчас.
        Args:
            current_user: User + Profile текущего пользователя
        Returns:
            ViewGetFreeCardUseCaseResponse:
                - get_free_card (GetFreeCardDTO): DTO со списками классов, редкостей и флагом can_get_free_card.
                - response_type (str): статус ответа
        Note:
           - SUCCESS: успешное получение данных.
           - SERVER_ERROR: любая непредвиденная ошибка.
        """

        try:
            data_for_page: dict = await get_rarities_and_classes(session_db=self.session_db)
            all_classes: list = data_for_page['classes']
            all_rarities: list = data_for_page['rarities']

            classes_card = [
                ClassCard(name=class_card.name, skill_description=class_card.description)
                for class_card in all_classes
            ]

            rarities_card = [
                RarityCard(name=rarity_card.name, chance_drop=rarity_card.drop_chance)
                for rarity_card in all_rarities
            ]

            can_get_card: bool = False
            if current_user and current_user.profile.receiving_timer is not None:
                hours_for_get_free_card = 6
                check_time, _ = time_difference_check(
                    check_time=current_user.profile.receiving_timer,
                    need_hours=hours_for_get_free_card
                )
                if check_time:
                    can_get_card = True
            elif current_user:
                can_get_card = True
            else:
                can_get_card = False

            return ViewGetFreeCardUseCaseResponse(
                response_type=ResponseType.SUCCESS,
                get_free_card=GetFreeCardDTO(
                    all_classes=classes_card,
                    all_rarities=rarities_card,
                    can_get_free_card=can_get_card
                )
            )
        except Exception as error:
            logger.error(f'Непредвиденная ошибка в ViewGetFreeCardUseCase: {error}', exc_info=True)
            return ViewGetFreeCardUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                get_free_card=None
            )


class GetFreeCardUseCase:
    """ Use case для получения случайной карты пользователем. """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            current_user_id: int | None
    ) -> GetFreeCardUseCaseResponse:
        """
        Выполняет получение бесплатной карты для авторизованного пользователя.
        Проверяет авторизацию, таймер ожидания, наличие слотов.
        Затем генерирует карту и создает запись в истории получения.
        Args:
            current_user_id: ID User текущего пользователя или None
        Returns:
            GetFreeCardUseCaseResponse:
                - new_card_id (int | None): ID новой карты (при успехе)
                - error_message (str | None): сообщение об ошибке
                - response_type (str): статус ответа.
        Raises:
           CooldownNotElapsedError: если не прошло достаточно времени.
        Note:
           - REDIRECT_WITH_INFO: успешное получение данных и перенаправление.
           - REDIRECT_WITH_ERROR: перенаправление с ошибкой.
           - UNAUTHORIZED: неавторизованный пользователь.
           - SERVER_ERROR: любая другая непредвиденная ошибка.
        """

        hours_for_get_free_card = 6

        if current_user_id is None:
            logger.warning(f'Попытка неавторизованного пользователя получить бесплатную карту')
            return GetFreeCardUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                new_card_id=None,
                error_message=f'Для получения бесплатной карты вы должны быть авторизованы'
            )

        await get_profile_for_update(session_db=self.session_db, user_id=current_user_id)
        current_user = await get_user_with_profile(session_db=self.session_db, user_id=current_user_id)

        if current_user is None:
            logger.warning(f'Попытка неавторизованного пользователя получить бесплатную карту')
            return GetFreeCardUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                new_card_id=None,
                error_message=f'Для получения бесплатной карты вы должны быть авторизованы'
            )
        try:
            # Получение и блокировка данных для транзакции
            if current_user.profile.receiving_timer is not None:
                check_time, hours = time_difference_check(
                    check_time=current_user.profile.receiving_timer,
                    need_hours=hours_for_get_free_card
                )
                if not check_time:
                    base_message = f'Вы не можете получить бесплатную карту'
                    logger.warning(f'Попытка пользователя {current_user.id} получить бесплатную карту, '
                                   f'но прошло недостаточно времени. Осталось: {hours}')
                    raise CooldownNotElapsedError(base_message=base_message, hours=hours)

            await check_can_user_receive_card(
                session_db=self.session_db,
                current_user=current_user,
                need_slots=1
            )
            await update_user_receiving_timer(
                session_db=self.session_db,
                current_user=current_user
            )
            new_card_id: int = await generate_random_card(
                session_db=self.session_db,
                owner_id=current_user.profile.id
            )
            await create_record_in_history_receiving_card(
                session_db=self.session_db,
                card_id=new_card_id,
                user_profile_id=current_user.profile.id,
                method_receiving='Генерация'
            )
            await self.session_db.commit()

            return GetFreeCardUseCaseResponse(
                response_type=ResponseType.REDIRECT_WITH_INFO,
                new_card_id=new_card_id,
                error_message=None
            )

        except (NotEnoughSlotsError, CooldownNotElapsedError) as error:
            await self.session_db.rollback()

            return GetFreeCardUseCaseResponse(
                response_type=error.response_type,
                new_card_id=None,
                error_message=str(error)
            )

        except Exception as error:
            await self.session_db.rollback()
            logger.error(f'Непредвиденная ошибка в GetFreeCardUseCase: {error}', exc_info=True)
            return GetFreeCardUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                new_card_id=None,
                error_message=None
            )


class ViewUserCardsUseCase:
    """ Use case для просмотра всех карт пользователя """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            user_id: int
    ) -> ViewUserCardsUseResponse:
        """
        Получает список всех карт пользователя.
        Args:
           user_id: ID User владельца карт.
        Returns:
           ViewUserCardsUseResponse:
               - user_cards_dto (UserCardsDTO | None): DTO с данными карт.
               - error_message (str | None): текст ошибки, если произошла.
               - response_type (str): статус ответа.
        Note:
           - SUCCESS: успешное получение данных.
           - NOT_FOUND: пользователь не найден.
           - SERVER_ERROR: любая другая непредвиденная ошибка.
        """

        try:
            owner: User = await get_base_info_profile(session_db=self.session_db, user_id=user_id)

            user_cards: list = await get_all_cards_user(
                session_db=self.session_db,
                owner_id=owner.profile.id,
                with_details=True)
            user_cards_dto = UserCardsDTO(
                cards=[
                    CardDTO(
                        id=card.id,
                        class_card_name=card.class_card.name,
                        rarity_card_name=card.rarity_card.name,
                        type_card_name=card.type_card.name,
                        class_card_pic=card.class_card.image,
                        hp=card.hp,
                        damage=card.damage,
                        level=card.level,
                        max_level=card.rarity_card.max_level,
                        merger=card.merger,
                        max_merger=card.max_merger,
                        enhancement=card.enhancement,
                        max_enhancement=card.max_enhancement,
                        sale_status=card.sale_status,
                        price=card.price,
                    )
                    for card in user_cards
                ],
                owner_id=owner.id,
                owner_username=owner.username,
                owner_current_card_id=owner.profile.current_card_id
            )
            return ViewUserCardsUseResponse(
                response_type=ResponseType.SUCCESS,
                error_message=None,
                user_cards=user_cards_dto
            )

        except UserNotFoundError as error:
            return ViewUserCardsUseResponse(
                response_type=ResponseType.NOT_FOUND,
                error_message=str(error),
                user_cards=None
            )

        except Exception as error:
            logger.error(f'Непредвиденная ошибка в ViewUserCardsUseCase: {error}', exc_info=True)
            return ViewUserCardsUseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                user_cards=None
            )


class ViewTradingUseCase:
    """ Use case для просмотра торговой площадки """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self) -> ViewTradingUseCaseResponse:
        """
        Получает все карты, которые продаются пользователями.
        Returns:
           ViewTradingUseCaseResponse:
               - cards_trading (CardsTradingDTO | None): DTO с данными карт, выставленных на продажу пользователями.
               - response_type (str): статус ответа.
        Note:
           - SUCCESS: успешное получение данных.
           - SERVER_ERROR
        """

        try:
            cards_trading: list = await get_cards_in_trading(session_db=self.session_db)
            cards_trading_dto = CardsTradingDTO(
                cards=[
                    CardDTO(
                        id=card.id,
                        class_card_name=card.class_card.name,
                        rarity_card_name=card.rarity_card.name,
                        type_card_name=card.type_card.name,
                        class_card_pic=card.class_card.image,
                        hp=card.hp,
                        damage=card.damage,
                        level=card.level,
                        max_level=card.rarity_card.max_level,
                        merger=card.merger,
                        max_merger=card.max_merger,
                        enhancement=card.enhancement,
                        max_enhancement=card.max_enhancement,
                        sale_status=card.sale_status,
                        price=card.price,
                        owner_id=card.owner.user.id,
                        owner_username=card.owner.user.username
                    )
                    for card in cards_trading
                ],
            )

            return ViewTradingUseCaseResponse(
                response_type=ResponseType.SUCCESS,
                cards_trading=cards_trading_dto
            )
        except Exception as error:
            logger.error(f'Непредвиденная ошибка в ViewTradingUseCase: {error}', exc_info=True)
            return ViewTradingUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                cards_trading=None
            )


class ViewMergeUseCase:
    """ Use case для просмотра доступных карт для слияния """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            current_card_id: int,
            current_user: User | None
    ) -> ViewMergeUseCaseResponse:
        """
        Выполняет получение карт для слияния.
        Args:
           current_user: User + Profile текущего пользователя
           current_card_id: ID текущей карты
        Returns:
           ViewMergeUseCaseResponse:
               - merge (CardsForMergeDTO | None): DTO с данными карт для слияния.
               - response_type (str): статус ответа.
               - error_message (str): сообщение об ошибке
        Note:
           - SUCCESS: успешное получение данных.
           - FORBIDDEN: нет прав.
           - UNAUTHORIZED: не авторизован.
           - NOT_FOUND: карта не найдена.
           - REDIRECT_WITH_ERROR: если слияние невозможно (например достигнут максимальный уровень)
           - SERVER_ERROR: любая другая непредвиденная ошибка.
        """

        if current_user is None:
            logger.warning(f'Попытка неавторизованного пользователя просмотреть меню слияния карты')
            return ViewMergeUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для слияния карты вы должны быть авторизованы',
                merge=None
            )

        try:
            current_card, cards_for_merge = await get_cards_for_merge(
                session_db=self.session_db,
                current_card_id=current_card_id,
                owner_id=current_user.profile.id
            )
            if current_card.merger >= current_card.max_merger:
                return ViewMergeUseCaseResponse(
                    response_type=ResponseType.REDIRECT_WITH_ERROR,
                    error_message=f'Карта уже имеет максимальный уровень слияния',
                    merge=None
                )

            current_card_dto = OneCardForMergeDTO(
                id=current_card.id,
                class_card_name=current_card.class_card.name,
                rarity_card_name=current_card.rarity_card.name,
                type_card_name=current_card.type_card.name,
                class_card_pic=current_card.class_card.image,
                hp=current_card.hp,
                damage=current_card.damage,
                level=current_card.level,
                max_level=current_card.rarity_card.max_level,
                merger=current_card.merger,
                max_merger=current_card.max_merger,
                enhancement=current_card.enhancement,
                max_enhancement=current_card.max_enhancement
            )

            cards_dto = [
                OneCardForMergeDTO(
                    id=card.id,
                    class_card_name=card.class_card.name,
                    rarity_card_name=card.rarity_card.name,
                    type_card_name=card.type_card.name,
                    class_card_pic=card.class_card.image,
                    hp=current_card.hp,
                    damage=current_card.damage,
                    level=card.level,
                    max_level=card.rarity_card.max_level,
                    merger=card.merger,
                    max_merger=card.max_merger,
                    enhancement=card.enhancement,
                    max_enhancement=card.max_enhancement
                )
                for card in cards_for_merge
            ]
            merge_dto = CardsForMergeDTO(
                current_card=current_card_dto,
                cards=cards_dto,
                need_cards=current_card.max_merger - current_card.merger
            )

            return ViewMergeUseCaseResponse(
                response_type=ResponseType.SUCCESS,
                error_message=None,
                merge=merge_dto
            )

        except (NotCardOwnerError, CardNotFoundError) as error:
            return ViewMergeUseCaseResponse(
                response_type=error.response_type,
                error_message=str(error),
                merge=None
            )

        except Exception as error:
            logger.error(f'Непредвиденная ошибка в ViewMergeUseCase: {error}', exc_info=True)
            return ViewMergeUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                merge=None
            )


class MergeUseCase:
    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            current_card_id: int,
            current_user_id: int | None,
            cards_for_merge: list[int]
    ) -> MergeUseCaseResponse:
        """
        Выполняет процесс слияния карты. В зависимости от количества слитых (удаленных) карт
        повышается уровень слияния.
        Если количество выбранных карт больше чем требуется, или выбраны недоступные карты,
        то возвращается ошибка, а слияния не происходит.
        Args:
           current_user_id: ID User текущего пользователя
           current_card_id: ID текущей карты
           cards_for_merge: список ID карт для слияния
        Returns:
           MergeUseCaseResponse:
               - response_type (str): статус ответа.
               - error_message (str): сообщение об ошибке
        Note:
           - REDIRECT_WITH_INFO: успешное получение данных.
           - UNAUTHORIZED: пользователь не авторизован.
           - FORBIDDEN: нет прав.
           - NOT_FOUND: карта(ы) не найдена(ы)
           - SERVER_ERROR: любая другая непредвиденная ошибка.
        """

        if current_user_id is None:
            logger.warning(f'Попытка неавторизованного пользователя слить карты')
            return MergeUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для слияния карты вы должны быть авторизованы',
                success_message=None
            )
        await get_profile_for_update(session_db=self.session_db, user_id=current_user_id)
        current_user = await get_user_with_profile(session_db=self.session_db, user_id=current_user_id)

        if current_user is None:
            logger.warning(f'Попытка неавторизованного пользователя получить бесплатную карту')
            return MergeUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для слияния карты вы должны быть авторизованы',
                success_message=None
            )

        try:
            await merge_card(
                session_db=self.session_db,
                current_card_id=current_card_id,
                cards_for_merge_ids=cards_for_merge,
                owner_id=current_user.profile.id)
            await self.session_db.commit()
            return MergeUseCaseResponse(
                response_type=ResponseType.REDIRECT_WITH_INFO,
                error_message=None,
                success_message=f'Вы успешно повысили уровень слияния карты'
            )

        except (CardNotFoundError, NotCardOwnerError, TooManyCardsMergeError, SelfMergeError) as error:
            await self.session_db.rollback()
            return MergeUseCaseResponse(
                response_type=error.response_type,
                error_message=str(error),
                success_message=None
            )

        except Exception as error:
            await self.session_db.rollback()
            logger.error(f'Непредвиденная ошибка в MergeUseCase: {error}', exc_info=True)
            return MergeUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                success_message=None
            )


class ViewUpgradeUseCase:
    """ Use case для просмотра меню усиления карты """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            current_card_id: int,
            current_user: User | None
    ) -> ViewUpgradeUseCaseResponse:
        """
        Выполняет получение карты и формирует DTO для отображения.
        Args:
           current_user: User + Profile текущего пользователя
           current_card_id: ID текущей карты
        Returns:
           ViewUpgradeUseCaseResponse:
               - upgrade_info (FullInfoUpgradingDTO | None): DTO с информацией для усиления карты
               - response_type (str): статус ответа.
               - error_message (str): сообщение об ошибке
        Note:
           - SUCCESS: успешное получение данных.
           - UNAUTHORIZED: пользователь не авторизован
           - FORBIDDEN: нет прав.
           - NOT_FOUND: карта не найдена
           - SERVER_ERROR: любая другая непредвиденная ошибка.
        """

        if current_user is None:
            logger.warning(f'Для просмотра меню усиления карт, вы должны быть авторизованы')
            return ViewUpgradeUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для усиления карты вы должны быть авторизованы',
                upgrade_info=None,
            )

        try:
            current_card = await get_card_with_details(session_db=self.session_db, card_id=current_card_id)
            if current_card.enhancement >= current_card.max_enhancement:
                return ViewUpgradeUseCaseResponse(
                    response_type=ResponseType.REDIRECT_WITH_ERROR,
                    error_message=f'Карта уже имеет максимальный уровень усиления',
                    upgrade_info=None,
                )
            if current_card.owner_id != current_user.profile.id:
                return ViewUpgradeUseCaseResponse(
                    response_type=ResponseType.FORBIDDEN,
                    error_message=f'Вы не являетесь владельцем этой карты',
                    upgrade_info=None,
                )

            current_card_dto = CardUpgradingDTO(
                id=current_card.id,
                class_card_name=current_card.class_card.name,
                rarity_card_name=current_card.rarity_card.name,
                type_card_name=current_card.type_card.name,
                hp=current_card.hp,
                damage=current_card.damage,
                class_card_pic=current_card.class_card.image,
                enhancement=current_card.enhancement,
                max_enhancement=current_card.max_enhancement
            )

            upgrade_items: list = await get_upgrade_items_in_user_inventory(
                session_db=self.session_db,
                owner_id=current_user.profile.id
            )

            upgrade_items_dto = [UpgradeItemsInventoryDTO(
                id=item.upgrade_item_type.id,
                name=item.upgrade_item_type.name,
                description=item.upgrade_item_type.description,
                image=item.upgrade_item_type.image,
                gold_for_use=item.upgrade_item_type.price_of_use,
                amount=item.amount)
                for item in upgrade_items
            ]
            upgrade_dto = FullInfoUpgradingDTO(card=current_card_dto, upgrade_items=upgrade_items_dto)

            return ViewUpgradeUseCaseResponse(
                response_type=ResponseType.SUCCESS,
                error_message=None,
                upgrade_info=upgrade_dto,
            )

        except (CardNotFoundError,) as error:
            return ViewUpgradeUseCaseResponse(
                response_type=error.response_type,
                error_message=str(error),
                upgrade_info=None,
            )

        except Exception as error:
            logger.error(f'Непредвиденная ошибка в ViewUpgradeUseCase: {error}', exc_info=True)
            return ViewUpgradeUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                upgrade_info=None,
            )


class UpgradeUseCase:
    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            current_card_id: int,
            current_user_id: int | None,
            upgrade_item_id: int
    ) -> UpgradeUseCaseResponse:
        """
        Улучшение карты с помощью предмета усиления
        Args:
           current_user_id: ID User текущего пользователя
           current_card_id: ID текущей карты
           upgrade_item_id: ID предмета усиления в инвентаре
        Returns:
           UpgradeUseCaseResponse:
               - response_type (str): статус ответа.
               - error_message (str | None): сообщение об ошибке
               - success (bool): флаг о успехе
               - success_message (str | NOne): сообщение об успехе
               - current_user_dto (CurrentUserForMenuDTO | None):  DTO текущего пользователя
        Note:
            - REDIRECT_WITH_INFO: успешное получение данных.
            - UNAUTHORIZED: не авторизован.
            - FORBIDDEN: нет прав.
            - REDIRECT_WITH_ERROR: не хватает ресурсов.
            - NOT_FOUND: карта или предмет не найден.
            - SERVER_ERROR: любая другая непредвиденная ошибка.
        """

        if current_user_id is None:
            logger.warning(f'Попытка неавторизованного пользователя усилить карту')
            return UpgradeUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для усиления карты вы должны быть авторизованы',
                success_message=None,
                current_user=None
            )
        await get_profile_for_update(session_db=self.session_db, user_id=current_user_id)
        current_user = await get_user_with_profile(session_db=self.session_db, user_id=current_user_id)

        if current_user is None:
            logger.warning(f'Попытка неавторизованного пользователя усилить карту')
            return UpgradeUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для усиления карты вы должны быть авторизованы',
                success_message=None,
                current_user=None
            )
        else:
            current_user_dto = await user_info_to_dto(user=current_user)
        try:
            price: int = await upgrade_card(
                session_db=self.session_db,
                card_id=current_card_id,
                upgrade_item_id=upgrade_item_id,
                user=current_user
            )
            for_transaction: dict = await charge_user_gold(
                session_db=self.session_db,
                current_user=current_user,
                need_gold=price
            )
            await create_transaction(
                session_db=self.session_db,
                gold_before=for_transaction['gold_before'],
                gold_after=for_transaction['gold_after'],
                user_profile_id=current_user.profile.id,
                comment='Усиление карты'
            )

            await self.session_db.commit()
            return UpgradeUseCaseResponse(
                response_type=ResponseType.REDIRECT_WITH_INFO,
                error_message=None,
                success_message=f'Вы успешно улучшили карту',
                current_user=current_user_dto
            )

        except (NotEnoughUpgradeItemsError, NotCardOwnerError, CardNotFoundError,
                MaxUpgradeCardError, InsufficientFundsUserError) as error:
            await self.session_db.rollback()
            return UpgradeUseCaseResponse(
                response_type=error.response_type,
                error_message=str(error),
                success_message=None,
                current_user=current_user_dto
            )

        except Exception as error:
            await self.session_db.rollback()
            logger.error(f'Непредвиденная ошибка в UpgradeUseCase: {error}', exc_info=True)
            return UpgradeUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                success_message=None,
                current_user=current_user_dto
            )
