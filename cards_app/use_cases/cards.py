import logging

from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.schemas import CardUpgradingDTO, UpgradeItemsInventoryDTO, FullInfoUpgradingDTO
from cards_app.services.inventory import get_upgrade_items_in_user_inventory
from cards_app.services.users import get_user_with_profile, user_info_to_dto, get_profile_for_update
from cards_app.types import (ViewCardUseCaseDict, ViewGetFreeCardUseCaseDict, GetFreeCardUseCaseDict,
                             ViewUserCardsUseCaseDict, ViewTradingUseCaseDict, ViewMergeUseCaseDict, MergeUseCaseDict,
                             ViewUpgradeUseCaseDict, UpgradeUseCaseDict)
from cards_app.exeptions import (NotEnoughSlotsError, CooldownNotElapsedError, CardNotFoundError, NotCardOwnerError,
                                 TooManyCardsMergeError, SelfMergeError, NotEnoughUpgradeItemsError,
                                 InsufficientFundsUserError, MaxUpgradeCardError)
from cards_app.services.cards import (get_card_with_details, get_rarities_and_classes, generate_random_card,
                                      create_record_in_history_receiving_card, get_all_cards_user, get_cards_in_trading,
                                      get_cards_for_merge, merge_card)
from cards_app.services.inventory import upgrade_card

from cards_app.schemas.cards import (AmuletDTO, CardInfoDTO, CardDTO, GetFreeCardDTO, RarityCard, ClassCard,
                                     UserCardsDTO, CardsTradingDTO, OneCardForMergeDTO, CardsForMergeDTO)
from cards_app.services.profile import (update_user_receiving_timer, check_can_user_receive_card, get_base_info_profile,
                                        charge_user_gold, create_transaction)

from cards_app.utils.common import calculate_need_exp, time_difference_check
from cards_app.models.users import User

logger = logging.getLogger(__name__)


class ViewCardUseCase:
    """ Use case для просмотра информации о конкретной карте """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, card_id: int, current_user: User | None
                      ) -> ViewCardUseCaseDict:
        """ Выполняет получение карты и формирует DTO для отображения.
               Args:
                   card_id: ID карты для просмотра.
                   current_user: User + Profile текущего пользователя
               Returns:
                   ViewCardUseCaseDict:
                       - card_info_dto (CardInfoDTO | None): DTO с данными карты, амулета и флагом владельца.
                       - error_message (str | None): текст ошибки, если произошла.
                       - status_code (int): HTTP статус-код.
               Note:
                   - 200: успешное получение данных.
                   - 404: карта не найдена.
                   - 500: любая другая непредвиденная ошибка.
               """

        answer_data: ViewCardUseCaseDict = {'card_info_dto': None,
                                            'error_message': None,
                                            'status_code': None,
                                            }
        try:
            card = await get_card_with_details(session_db=self.session_db,
                                               card_id=card_id)

        except CardNotFoundError as error:
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code
            return answer_data

        except Exception as error:
            answer_data['error_message'] = f'Упс, произошла непредвиденная ошибка. Попробуйте позже :('
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в ViewCardUseCase: {error}', exc_info=True)
            return answer_data

        need_exp: int = calculate_need_exp(level=card.level)
        card_dto = CardDTO(id=card.id,
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
                           need_exp=need_exp)

        amulet_dto = None
        if card.amulet:
            amulet_dto = AmuletDTO(id=card.amulet.id,
                                   name=card.amulet.amulet_type.name,
                                   bonus_hp=card.amulet.amulet_type.bonus_hp,
                                   bonus_damage=card.amulet.amulet_type.bonus_damage,
                                   )

        if current_user:
            is_owner = True if current_user.profile.id == card.owner_id else False
        else:
            is_owner = False

        card_info_dto = CardInfoDTO(card=card_dto,
                                    amulet=amulet_dto,
                                    is_owner=is_owner
                                    )
        answer_data['card_info_dto'] = card_info_dto
        answer_data['status_code'] = 200
        return answer_data


class ViewGetFreeCardUseCase:
    """ Use case для просмотра страницы с получением бесплатной карты.
        Показывает списки всех классов и редкостей, а также флаг возможности получить карту сейчас.
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user: User | None
                      ) -> ViewGetFreeCardUseCaseDict:
        """ Формирует DTO для страницы получения бесплатной карты.
            Args:
                current_user: User + Profile текущего пользователя
            Returns:
                ViewGetFreeCardUseCaseDict:
                    - get_free_card_dto (GetFreeCardDTO): DTO со списками классов, редкостей и флагом can_get_free_card.
                    - status_code (int): HTTP статус-код всегда 200
        """

        answer_data = {'get_free_card_dto': None,
                       'status_code': 200}

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
            check_time, _ = time_difference_check(check_time=current_user.profile.receiving_timer,
                                                  need_hours=hours_for_get_free_card)
            if check_time:
                can_get_card = True
        elif current_user:
            can_get_card = True
        else:
            can_get_card = False

        answer_data['get_free_card_dto'] = GetFreeCardDTO(all_classes=classes_card,
                                                          all_rarities=rarities_card,
                                                          can_get_free_card=can_get_card)
        return answer_data


class GetFreeCardUseCase:
    """ Use case для получения случайной карты пользователем.
        Проверяет авторизацию, таймер ожидания, наличие слотов, генерирует карту и записывает историю.
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user_id: int | None
                      ) -> GetFreeCardUseCaseDict:
        """ Выполняет получение бесплатной карты для авторизованного пользователя.
            Args:
                current_user_id: ID User текущего пользователя или None
            Returns:
                GetFreeCardUseCaseDict:
                    - success (bool): True при успешном получении карты
                    - new_card_id (int | None): ID новой карты (при успехе)
                    - error_message (str | None): сообщение об ошибке
                    - status_code (int): HTTP статус-код
                    - current_user_dto (CurrentUserForMenuDTO | None): DTO текущего пользователя
           Note:
               - 303: успешное получение данных и перенаправление
               - 400: ошибка доступа
               - 500: любая другая непредвиденная ошибка
        """

        hours_for_get_free_card = 6
        answer_data = {'success': None,
                       'new_card_id': None,
                       'error_message': None,
                       'status_code': None,
                       'current_user_dto': None}

        if current_user_id is None:
            answer_data['success'] = False
            answer_data['error_message'] = f'Для получения бесплатной карты вы должны быть авторизованы'
            answer_data['status_code'] = 400
            logger.warning(f'Попытка неавторизованного пользователя получить бесплатную карту')
            return answer_data
        try:
            # Получение и блокировка данных для транзакции
            await get_profile_for_update(session_db=self.session_db,
                                         user_id=current_user_id)
            # current_user получит профиль из сессии при запросе (используется для создания DTO)
            current_user = await get_user_with_profile(session_db=self.session_db,
                                                       user_id=current_user_id)
            if current_user:
                answer_data['current_user_dto'] = await user_info_to_dto(user=current_user)
            else:
                answer_data['success'] = False
                answer_data['error_message'] = f'Для получения бесплатной карты вы должны быть авторизованы'
                answer_data['status_code'] = 400
                logger.warning(f'Попытка неавторизованного пользователя получить бесплатную карту')
                return answer_data

            if current_user.profile.receiving_timer is not None:
                check_time, hours = time_difference_check(check_time=current_user.profile.receiving_timer,
                                                          need_hours=hours_for_get_free_card)
                if not check_time:
                    base_message = f'Вы не можете получить бесплатную карту'
                    logger.warning(f'Попытка пользователя {current_user.id} получить бесплатную карту, '
                                   f'но прошло недостаточно времени. Осталось: {hours}')
                    raise CooldownNotElapsedError(base_message=base_message, hours=hours)

            await check_can_user_receive_card(session_db=self.session_db,
                                              current_user=current_user,
                                              need_slots=1)
            await update_user_receiving_timer(session_db=self.session_db,
                                              current_user=current_user)
            new_card_id = await generate_random_card(session_db=self.session_db,
                                                     owner_id=current_user.profile.id)
            await create_record_in_history_receiving_card(session_db=self.session_db,
                                                          card_id=new_card_id,
                                                          user_profile_id=current_user.profile.id,
                                                          method_receiving='Генерация')
            await self.session_db.commit()
            answer_data['success'] = True
            answer_data['new_card_id'] = new_card_id
            answer_data['status_code'] = 303

        except (NotEnoughSlotsError, CooldownNotElapsedError) as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = f'Упс, произошла непредвиденная ошибка. Попробуйте позже :('
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в GetFreeCardUseCase: {error}', exc_info=True)

        return answer_data


class ViewUserCardsUseCase:
    """ Use case для просмотра карт пользователя """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, user_id: int
                      ) -> ViewUserCardsUseCaseDict:
        """ Выполняет получение карты и формирует DTO для отображения.
               Args:
                   user_id: ID User владельца карт.
               Returns:
                   ViewUserCardsUseCaseDict:
                       - user_cards_dto (CardInfoDTO | None): DTO с данными карты, амулета и флагом владельца.
                       - error_message (str | None): текст ошибки, если произошла.
                       - status_code (int): HTTP статус-код.
               Note:
                   - 200: успешное получение данных.
                   - 404: пользователь не найден (UserNotFound).
                   - 500: любая другая непредвиденная ошибка.
               """

        answer_data: ViewUserCardsUseCaseDict = {'user_cards_dto': None,
                                                 'error_message': None,
                                                 'status_code': None,
                                                 }
        try:
            owner: User = await get_base_info_profile(session_db=self.session_db,
                                                      user_id=user_id)
        except CardNotFoundError as error:
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code
            return answer_data
        except Exception as error:
            answer_data['error_message'] = f'Упс, произошла непредвиденная ошибка. Попробуйте позже :('
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в ViewUserCardsUseCase: {error}', exc_info=True)
            return answer_data

        user_cards: list = await get_all_cards_user(session_db=self.session_db,
                                                    owner_id=owner.profile.id,
                                                    with_details=True)
        user_cards_dto = UserCardsDTO(
            cards=[
                CardDTO(id=card.id,
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
        answer_data['user_cards_dto'] = user_cards_dto
        answer_data['status_code'] = 200
        return answer_data


class ViewTradingUseCase:
    """ Use case для просмотра торговой площадки """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self) -> ViewTradingUseCaseDict:
        """ Выполняет получение карты и формирует DTO для отображения.
               Returns:
                   ViewTradingUseCaseDict:
                       - cards_trading_dto (CardInfoDTO | None): DTO с данными карты, амулета и флагом владельца.
                       - status_code (int): HTTP статус-код.
               Note:
                   - 200: успешное получение данных.
                   - 500: любая другая непредвиденная ошибка.
               """

        answer_data: ViewTradingUseCaseDict = {'cards_trading_dto': None,
                                               'status_code': None}

        cards_trading: list = await get_cards_in_trading(session_db=self.session_db)
        cards_trading_dto = CardsTradingDTO(
            cards=[
                CardDTO(id=card.id,
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
        answer_data['cards_trading_dto'] = cards_trading_dto
        answer_data['status_code'] = 200
        return answer_data


class ViewMergeUseCase:
    """ Use case для просмотра доступных карт для слияния """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      current_card_id: int,
                      current_user: User | None
                      ) -> ViewMergeUseCaseDict:
        """ Выполняет получение карты и формирует DTO для отображения.
               Args:
                   current_user: User + Profile текущего пользователя
                   current_card_id: ID текущей карты
               Returns:
                   ViewMergeUseCaseDict:
                       - merge_dto (CardsForMergeDTO | None): DTO с данными карты, амулета и флагом владельца.
                       - status_code (int): HTTP статус-код.
                       - error_message (str): сообщение об ошибке
               Note:
                   - 200: успешное получение данных.
                   - 400: нет прав или пользователь не авторизован
                   - 404: карта не найдена
                   - 500: любая другая непредвиденная ошибка.
               """

        answer_data = {'merge_dto': None,
                       'status_code': None,
                       'error_message': None}

        if current_user is None:
            answer_data['status_code'] = 400
            answer_data['error_message'] = f'Для слияния карты вы должны быть авторизованы'
            logger.warning(f'Попытка неавторизованного пользователя просмотреть меню слияния карты')
            return answer_data

        try:
            current_card, cards_for_merge = await get_cards_for_merge(session_db=self.session_db,
                                                                      current_card_id=current_card_id,
                                                                      owner_id=current_user.profile.id)
            if current_card.merger >= current_card.max_merger:
                answer_data['status_code'] = 400
                answer_data['error_message'] = f'Карта уже имеет максимальный уровень слияния'
                return answer_data

            current_card_dto = OneCardForMergeDTO(id=current_card.id,
                                                  class_card_name=current_card.class_card.name,
                                                  rarity_card_name=current_card.rarity_card.name,
                                                  type_card_name=current_card.type_card.name,
                                                  class_card_pic=current_card.class_card.image,
                                                  level=current_card.level,
                                                  max_level=current_card.rarity_card.max_level,
                                                  merger=current_card.merger,
                                                  max_merger=current_card.max_merger,
                                                  enhancement=current_card.enhancement,
                                                  max_enhancement=current_card.max_enhancement)

            cards_dto = [OneCardForMergeDTO(id=card.id,
                                            class_card_name=card.class_card.name,
                                            rarity_card_name=card.rarity_card.name,
                                            type_card_name=card.type_card.name,
                                            class_card_pic=card.class_card.image,
                                            level=card.level,
                                            max_level=card.rarity_card.max_level,
                                            merger=card.merger,
                                            max_merger=card.max_merger,
                                            enhancement=card.enhancement,
                                            max_enhancement=card.max_enhancement)
                         for card in cards_for_merge
                         ]
            merge_dto = CardsForMergeDTO(current_card=current_card_dto,
                                         cards=cards_dto,
                                         need_cards=current_card.max_merger-current_card.merger)

            answer_data['status_code'] = 200
            answer_data['merge_dto'] = merge_dto
            return answer_data

        except (NotCardOwnerError, CardNotFoundError) as error:
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            answer_data['error_message'] = f'Упс, произошла непредвиденная ошибка. Попробуйте позже :('
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в ViewMergeUseCase: {error}', exc_info=True)

        return answer_data


class MergeUseCase:
    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      current_card_id: int,
                      current_user_id: int | None,
                      cards_for_merge: list[int]
                      ) -> MergeUseCaseDict:
        """ Выполняет получение карты и формирует DTO для отображения.
               Args:
                   current_user_id: ID User текущего пользователя
                   current_card_id: ID текущей карты
                   cards_for_merge: список ID карт для слияния
               Returns:
                   MergeUseCaseDict:
                       - status_code (int): HTTP статус-код
                       - error_message (str): сообщение об ошибке
                       - current_user_dto (CurrentUserForMenuDTO | None): DTO текущего пользователя
               Note:
                   - 303: успешное получение данных.
                   - 400: нет прав или пользователь не авторизован
                   - 404: карта(ы) не найдена(ы)
                   - 500: любая другая непредвиденная ошибка.
               """

        answer_data = {'status_code': None,
                       'error_message': None,
                       'success': None,
                       'success_message': None,
                       'current_user_dto': None}

        if current_user_id is None:
            answer_data['success'] = False
            answer_data['error_message'] = f'Вы должны быть авторизованы'
            answer_data['status_code'] = 400
            logger.warning(f'Попытка неавторизованного пользователя слить карты')
            return answer_data

        try:
            await get_profile_for_update(session_db=self.session_db,
                                         user_id=current_user_id)
            # current_user получит профиль из сессии при запросе (используется для создания DTO)
            current_user = await get_user_with_profile(session_db=self.session_db,
                                                       user_id=current_user_id)

            if current_user:
                answer_data['current_user_dto'] = await user_info_to_dto(user=current_user)
            else:
                answer_data['success'] = False
                answer_data['error_message'] = f'Для слияния карты вы должны быть авторизованы'
                answer_data['status_code'] = 400
                logger.warning(f'Попытка неавторизованного пользователя повысить уровень слияния карты')
                return answer_data

            await merge_card(session_db=self.session_db,
                             current_card_id=current_card_id,
                             cards_for_merge_ids=cards_for_merge,
                             owner_id=current_user.profile.id)
            await self.session_db.commit()
            answer_data['success'] = True
            answer_data['status_code'] = 303
            answer_data['success_message'] = f'Вы успешно повысили уровень слияния карты'

        except (CardNotFoundError, NotCardOwnerError, TooManyCardsMergeError, SelfMergeError) as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = f'Упс, произошла непредвиденная ошибка. Попробуйте позже :('
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в MergeUseCase: {error}', exc_info=True)

        return answer_data


class ViewUpgradeUseCase:
    """ Use case для просмотра доступных карт для слияния """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      current_card_id: int,
                      current_user: User | None
                      ) -> ViewUpgradeUseCaseDict:
        """ Выполняет получение карты и формирует DTO для отображения.
               Args:
                   current_user: User + Profile текущего пользователя
                   current_card_id: ID текущей карты
               Returns:
                   ViewUpgradeUseCaseDict:
                       - upgrade_dto (FullInfoUpgradingDTO | None): DTO с информацией для усиления карты
                       - status_code (int): HTTP статус-код.
                       - error_message (str): сообщение об ошибке
               Note:
                   - 200: успешное получение данных.
                   - 400: нет прав или пользователь не авторизован
                   - 404: карта не найдена
                   - 500: любая другая непредвиденная ошибка.
               """

        answer_data = {'upgrade_dto': None,
                       'status_code': None,
                       'error_message': None}

        if current_user is None:
            answer_data['status_code'] = 400
            answer_data['error_message'] = f'Для усиления карты вы должны быть авторизованы'
            logger.warning(f'Для просмотра меню усиления карт, вы должны быть авторизованы')
            return answer_data

        try:
            current_card = await get_card_with_details(session_db=self.session_db,
                                                       card_id=current_card_id)
            if current_card.enhancement >= current_card.max_enhancement:
                answer_data['status_code'] = 400
                answer_data['error_message'] = f'Карта уже имеет максимальный уровень усиления'
                return answer_data
            if current_card.owner_id != current_user.profile.id:
                answer_data['status_code'] = 400
                answer_data['error_message'] = f'Вы не являетесь владельцем этой карты'
                return answer_data

            current_card_dto = CardUpgradingDTO(id=current_card.id,
                                                class_name=current_card.class_card.name,
                                                rarity_name=current_card.rarity_card.name,
                                                type_name=current_card.type_card.name,
                                                hp=current_card.hp,
                                                damage=current_card.damage,
                                                image=current_card.class_card.image,
                                                enhancement=current_card.enhancement,
                                                max_enhancement=current_card.max_enhancement)

            upgrade_items: list = await get_upgrade_items_in_user_inventory(session_db=self.session_db,
                                                                            owner_id=current_user.profile.id)

            upgrade_items_dto = [UpgradeItemsInventoryDTO(id=item.upgrade_item_type.id,
                                                          name=item.upgrade_item_type.name,
                                                          description=item.upgrade_item_type.description,
                                                          image=item.upgrade_item_type.image,
                                                          gold_for_use=item.upgrade_item_type.price_of_use,
                                                          amount=item.amount)
                                 for item in upgrade_items
                                 ]
            upgrade_dto = FullInfoUpgradingDTO(card=current_card_dto,
                                               upgrade_items=upgrade_items_dto,
                                               )

            answer_data['status_code'] = 200
            answer_data['upgrade_dto'] = upgrade_dto
            return answer_data

        except (CardNotFoundError, ) as error:
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            answer_data['error_message'] = f'Упс, произошла непредвиденная ошибка. Попробуйте позже :('
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в ViewUpgradeUseCase: {error}', exc_info=True)

        return answer_data


class UpgradeUseCase:
    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      current_card_id: int,
                      current_user_id: int | None,
                      upgrade_item_id: int
                      ) -> UpgradeUseCaseDict:
        """ Улучшение карты с помощью предмета усиления
               Args:
                   current_user_id: ID User текущего пользователя
                   current_card_id: ID текущей карты
                   upgrade_item_id: ID предмета усиления в инвентаре
               Returns:
                   UpgradeUseCaseDict:
                       - status_code (int): HTTP статус-код.
                       - error_message (str | None): сообщение об ошибке
                       - success (bool): флаг о успехе
                       - success_message (str | NOne): сообщение об успехе
                       - current_user_dto (CurrentUserForMenuDTO | None):  DTO текущего пользователя
               Note:
                   - 303: успешное получение данных.
                   - 400: нет прав или пользователь не авторизован или не хватает предметов
                   - 404: карта не найдена
                   - 500: любая другая непредвиденная ошибка.
               """

        answer_data = {'status_code': None,
                       'error_message': None,
                       'success': None,
                       'success_message': None,
                       'current_user_dto': None}

        if current_user_id is None:
            answer_data['success'] = False
            answer_data['error_message'] = f'Для усиления карты вы должны быть авторизованы'
            answer_data['status_code'] = 400
            logger.warning(f'Попытка неавторизованного пользователя усилить карту')
            return answer_data

        try:
            # Блокирует профиль, чтобы избежать гонок
            await get_profile_for_update(session_db=self.session_db,
                                         user_id=current_user_id)
            # current_user получит профиль из сессии при запросе (используется для создания DTO)
            current_user = await get_user_with_profile(session_db=self.session_db,
                                                       user_id=current_user_id)

            if current_user:
                answer_data['current_user_dto'] = await user_info_to_dto(user=current_user)
            else:
                answer_data['success'] = False
                answer_data['error_message'] = f'Для усиления карты вы должны быть авторизованы'
                answer_data['status_code'] = 400
                logger.warning(f'Попытка неавторизованного пользователя усилить карту')
                return answer_data

            price: int = await upgrade_card(session_db=self.session_db,
                                            card_id=current_card_id,
                                            upgrade_item_id=upgrade_item_id,
                                            user=current_user)
            for_transaction: dict = await charge_user_gold(session_db=self.session_db,
                                                           current_user=current_user,
                                                           need_gold=price)
            await create_transaction(session_db=self.session_db,
                                     gold_before=for_transaction['gold_before'],
                                     gold_after=for_transaction['gold_after'],
                                     user_profile_id=current_user.profile.id,
                                     comment='Усиление карты')

            await self.session_db.commit()
            answer_data['success'] = True
            answer_data['status_code'] = 303
            answer_data['success_message'] = f'Вы успешно улучшили карту'

        except (NotEnoughUpgradeItemsError, NotCardOwnerError, CardNotFoundError,
                MaxUpgradeCardError, InsufficientFundsUserError) as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = f'Упс, произошла непредвиденная ошибка. Попробуйте позже :('
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в UpgradeUseCase: {error}', exc_info=True)

        return answer_data
