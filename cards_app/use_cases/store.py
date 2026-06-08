import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from cards_app.exeptions import (InsufficientFundsUserError, NotEnoughSlotsError, CardNotOnSaleError,
                                 CardInStoreNotFoundError, BoxNotFoundError, ExpItemNotFoundError, AmuletNotFoundError,
                                 AmuletNotOnSaleError)
from cards_app.models import User
from cards_app.schemas.store import (CardInStoreDTO, CardStoreDTO, BoxStoreDTO, AllStoreDTO, AmuletsStoreDTO,
                                     UpgradeItemsStoreDTO, ExpItemsStoreDTO, ExpItemRewardDTO, OpenBoxExpItemDTO,
                                     OpenBoxAmuletDTO, AmuletRewardDTO)
from cards_app.services.cards import (get_temp_card_in_store, create_new_card_from_template,
                                      create_record_in_history_receiving_card)
from cards_app.services.profile import check_can_user_receive_card, charge_user_gold, create_transaction
from cards_app.services.store import (get_cards_in_store, get_box_in_store, get_amulets_in_store,
                                      get_upgrade_items_in_store, get_exp_items_in_store, get_box_info, open_box_card,
                                      open_box_exp_item, open_box_amulet, buy_exp_items, buy_amulet, buy_upgrade_item)
from cards_app.types import (ViewCardStoreUseCaseDict, BuyStoreCardUseCaseDict, ViewItemStoreUseCaseDict,
                             BuyBoxUseCaseDict, BuyItemUseCaseDict)
from cards_app.utils.common import calculate_final_price

logger = logging.getLogger(__name__)


class ViewCardStoreUseCase:
    """ Use case для просмотра магазина карт.
        Преобразует данные для вывода информации о продаваемых картах.
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self) -> ViewCardStoreUseCaseDict:
        """ Выполняет получение списка карт, доступных в магазине, и формирует DTO.
            Returns:
                ViewCardStoreUseCaseDict:
                    - status_code (int): HTTP статус-код.
                    - card_store_dto (CardStoreDTO | None): DTO со списком карт в магазине.
            Note:
                - 200: успешное получение данных.
                - 500: непредвиденная ошибка.
        """

        answer_data = {'status_code': None,
                       'card_store_dto': None}

        all_cards: list = await get_cards_in_store(session_db=self.session_db)
        cards_in_store = []
        for card in all_cards:
            cards_in_store.append(CardInStoreDTO(id=card.id,
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
        answer_data['status_code'] = 200
        answer_data['card_store_dto'] = card_store_dto

        return answer_data


class BuyStoreCardUseCase:
    """ Use case для покупки карты в магазине """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      current_user: User | None,
                      temp_card_id: int,
                      ) -> BuyStoreCardUseCaseDict:
        """ Выполняет покупку карты в магазине.
           Args:
               current_user: User + Profile текущего пользователя
               temp_card_id: ID карты-шаблона в магазине

           Returns:
               BuyStoreCardUseCaseDict:
                   - success (bool): True при успешной покупке.
                   - error_message (str | None): сообщение об ошибке.
                   - new_card_id (int | None): ID созданной карты (при успехе).
                   - status_code (int): HTTP статус-код.
           Note:
               - 303: успешная покупка (перенаправление).
               - 400: ошибка доступа
               - 500: непредвиденная ошибка.
           """

        answer_data = {'success': None,
                       'error_message': None,
                       'new_card_id': None,
                       'status_code': None}

        # Проверка, что пользователь авторизован
        if current_user is None:
            answer_data['success'] = False
            answer_data['error_message'] = f'Для покупки карты нужно быть авторизованным'
            answer_data['status_code'] = 400
            return answer_data
        try:
            # Проверка, что у пользователя хватает места
            await check_can_user_receive_card(session_db=self.session_db,
                                              current_user=current_user,
                                              need_slots=1)

            # Взятие карты из магазина
            card_temp = await get_temp_card_in_store(session_db=self.session_db,
                                                     card_temp_id=temp_card_id)
            if card_temp.discount_now:
                final_price_card = calculate_final_price(price=card_temp.price,
                                                         discount=card_temp.discount)
            else:
                final_price_card = card_temp.price

            # Снятие денег
            gold_transaction = await charge_user_gold(session_db=self.session_db,
                                                      current_user=current_user,
                                                      need_gold=final_price_card)

            # Создание карты
            new_card_id = await create_new_card_from_template(session_db=self.session_db,
                                                              owner_id=current_user.profile.id,
                                                              card_temp=card_temp)

            # Создание транзакции
            await create_transaction(session_db=self.session_db,
                                     user_profile_id=current_user.id,
                                     gold_before=gold_transaction['gold_before'],
                                     gold_after=gold_transaction['gold_after'],
                                     comment='Покупка в магазине карт')

            # Создание записи о получении карты
            await create_record_in_history_receiving_card(session_db=self.session_db,
                                                          card_id=new_card_id,
                                                          user_profile_id=current_user.profile.id,
                                                          method_receiving='Покупка в магазине')
            answer_data['success'] = True
            answer_data['new_card_id'] = new_card_id
            answer_data['status_code'] = 303
            await self.session_db.commit()

        except (NotEnoughSlotsError, InsufficientFundsUserError, CardNotOnSaleError, CardInStoreNotFoundError) as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в BuyStoreCardUseCase: {error}', exc_info=True)

        return answer_data


class ViewItemStoreUseCase:
    """ Use case для просмотра магазина предметов.
        Преобразует данные для вывода ассортимента магазина в зависимости от фильтра
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, store_filter: str) -> ViewItemStoreUseCaseDict:
        """ Выполняет получение списков предметов, доступных в магазине, и формирует DTO.
            Args:
               store_filter: фильтр магазина
            Returns:
                ViewItemStoreUseCaseDict:
                    - status_code (int): HTTP статус-код.
                    - store_dto (ItemStoreDTO | None): DTO  ассортиментов магазина
            Note:
                - 200: успешное получение данных.
                - 500: непредвиденная ошибка
        """

        answer_data: ViewItemStoreUseCaseDict = {'status_code': None,
                                                 'store_dto': None,
                                                 'error_message': None}

        if store_filter == 'box':
            store_dto = AllStoreDTO(boxes=await self._get_boxes_dto(),
                                    exp_items=None,
                                    amulets=None,
                                    upgrade_items=None
                                    )

        elif store_filter == 'amulet':
            store_dto = AllStoreDTO(boxes=None,
                                    exp_items=None,
                                    amulets=await self._get_amulets_dto(),
                                    upgrade_items=None
                                    )

        elif store_filter == 'upgrade_item':
            store_dto = AllStoreDTO(boxes=None,
                                    exp_items=None,
                                    amulets=None,
                                    upgrade_items=await self._get_upgrade_items_dto()
                                    )

        elif store_filter == 'exp_items':
            store_dto = AllStoreDTO(boxes=None,
                                    exp_items=await self._get_exp_items_dto(),
                                    amulets=None,
                                    upgrade_items=None
                                    )

        elif store_filter == 'all':
            box, exp, amu, upg = await asyncio.gather(self._get_boxes_dto(),
                                                      self._get_exp_items_dto(),
                                                      self._get_amulets_dto(),
                                                      self._get_upgrade_items_dto()
                                                      )
            store_dto = AllStoreDTO(boxes=box,
                                    exp_items=exp,
                                    amulets=amu,
                                    upgrade_items=upg
                                    )
        else:
            answer_data['status_code'] = 500
            answer_data['error_message'] = f'Неверный фильтр магазина'
            return answer_data

        answer_data['store_dto'] = store_dto
        answer_data['status_code'] = 200

        return answer_data

    async def _get_boxes_dto(self) -> list[BoxStoreDTO]:
        """ Преобразует DTO для сундуков """

        boxes: list = await get_box_in_store(session_db=self.session_db)
        boxes_dto = [BoxStoreDTO(id=box.id,
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
        amulets_dto = [AmuletsStoreDTO(id=amulet.id,
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
        upgrade_items_dto = [UpgradeItemsStoreDTO(id=item.id,
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
        exp_items_dto = [ExpItemsStoreDTO(id=item.id,
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

    async def execute(self,
                      current_user: User | None,
                      box_id: int) -> BuyBoxUseCaseDict:
        """ Выполняет
            Args:
               current_user: User + Profile
               box_id: ID сундука из магазина
            Returns:
                BuyBoxUseCaseDict:
                    - status_code (int): HTTP статус-код.
                    - store_dto (ItemStoreDTO | None): DTO  ассортиментов магазина
            Note:
                - 303: успешное получение данных.
                - 400: пользователь не авторизован ил не хватает денег
                - 404: не найден сундук
                - 500: непредвиденная ошибка
        """

        answer_data = {'status_code': None,
                       'error_message': None,
                       'exp_items_dto': None,
                       'amulets_items_dto': None,
                       'card_id': None}

        if current_user is None:
            answer_data['status_code'] = 400
            answer_data['error_message'] = f'Вы должны быть авторизованы'
            return answer_data

        try:
            box_info = await get_box_info(session_db=self.session_db, box_id=box_id)
            gold_transaction: dict = await charge_user_gold(session_db=self.session_db,
                                                            current_user=current_user,
                                                            need_gold=box_info.price)
            await create_transaction(session_db=self.session_db,
                                     user_profile_id=current_user.profile.id,
                                     gold_before=gold_transaction['gold_before'],
                                     gold_after=gold_transaction['gold_after'],
                                     comment='Покупка сундука')

            if box_info.reward_type == 'card':
                new_card_id: int = await open_box_card(session_db=self.session_db,
                                                       user=current_user)
                answer_data['card_id'] = new_card_id
                answer_data['status_code'] = 303

            elif box_info.reward_type == 'exp_item':
                exp_items: list = await open_box_exp_item(session_db=self.session_db,
                                                          user=current_user)
                exp_items_list = [ExpItemRewardDTO(name=item.name,
                                                   experience_amount=item.experience_amount,
                                                   image=item.image,
                                                   )
                                  for item in exp_items
                                  ]
                exp_items_dto = OpenBoxExpItemDTO(boxs=exp_items_list)
                answer_data['exp_items_dto'] = exp_items_dto
                answer_data['status_code'] = 303

            elif box_info.reward_type == 'amulet':
                amulets: list = await open_box_amulet(session_db=self.session_db,
                                                      user=current_user)
                amulets_list = [AmuletRewardDTO(name=amulet.name,
                                                bonus_hp=amulet.bonus_hp,
                                                bonus_damage=amulet.bonus_damage,
                                                image=amulet.image,
                                                rarity_name=amulet.rarity.name
                                                )
                                for amulet in amulets
                                ]
                amulets_dto = OpenBoxAmuletDTO(amulets=amulets_list)
                answer_data['amulets_items_dto'] = amulets_dto
                answer_data['status_code'] = 303

            await self.session_db.commit()
            return answer_data

        except (BoxNotFoundError, InsufficientFundsUserError, NotEnoughSlotsError) as error:
            await self.session_db.rollback()
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            await self.session_db.rollback()
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в BuyBoxUseCase: {error}', exc_info=True)

        return answer_data


class BuyExpItemUseCase:
    """ Use case для покупки книг опыта в магазине """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      current_user: User | None,
                      exp_item_id: int,
                      amount: int
                      ) -> BuyItemUseCaseDict:
        """ Выполняет
            Args:
               current_user: User + Profile
               exp_item_id: ID книги опыта
               amount: количество книг
            Returns:
                BuyItemUseCaseDict:
                    - status_code (int): HTTP статус-код.
                    - success (bool): флаг успеха покупки
                    - success_message (str | None):
                    - error_message (str | None): сообщение об ошибке
            Note:
                - 303: успешное получение данных.
                - 400: пользователь не авторизован ил не хватает денег
                - 404: не найдена книга
                - 500: непредвиденная ошибка
        """

        answer_data = {'status_code': None,
                       'error_message': None,
                       'success': None,
                       'success_message': None
                       }

        if current_user is None:
            answer_data['success'] = False
            answer_data['status_code'] = 400
            answer_data['error_message'] = f'Вы должны быть авторизованы'
            return answer_data

        try:
            await buy_exp_items(session_db=self.session_db,
                                exp_item_id=exp_item_id,
                                exp_item_amount=amount,
                                user=current_user)

            answer_data['status_code'] = 303
            answer_data['success'] = True
            answer_data['success_message'] = f'Вы успешно купили {amount} книг'
            await self.session_db.commit()

        except (InsufficientFundsUserError, ExpItemNotFoundError,) as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в BuyExpItemUseCase: {error}', exc_info=True)

        return answer_data


class BuyAmuletUseCase:
    """ Use case для покупки амулета в магазине """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      current_user: User | None,
                      amulet_id: int,
                      ) -> BuyItemUseCaseDict:
        """ Выполняет
            Args:
               current_user: User + Profile
               amulet_id: ID амулета
            Returns:
                BuyItemUseCaseDict:
                    - status_code (int): HTTP статус-код.
                    - success (bool): флаг успеха покупки
                    - success_message (str | None):
                    - error_message (str | None): сообщение об ошибке
            Note:
                - 303: успешное получение данных.
                - 400: пользователь не авторизован ил не хватает денег
                - 404: не найдена книга
                - 500: непредвиденная ошибка
        """

        answer_data = {'status_code': None,
                       'error_message': None,
                       'success': None,
                       'success_message': None
                       }

        if current_user is None:
            answer_data['success'] = False
            answer_data['status_code'] = 400
            answer_data['error_message'] = f'Вы должны быть авторизованы'
            return answer_data

        try:
            await buy_amulet(session_db=self.session_db,
                             amulet_id=amulet_id,
                             user=current_user)

            answer_data['status_code'] = 303
            answer_data['success'] = True
            answer_data['success_message'] = f'Вы успешно купили амулет'
            await self.session_db.commit()

        except (AmuletNotFoundError, AmuletNotOnSaleError, NotEnoughSlotsError,
                InsufficientFundsUserError, ) as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в BuyAmuletUseCase: {error}', exc_info=True)

        return answer_data


class BuyUpgradeItemUseCase:
    """ Use case для покупки предмета усиления в магазине """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      current_user: User | None,
                      upgrade_item_id: int,
                      ) -> BuyItemUseCaseDict:
        """ Выполняет
            Args:
               current_user: User + Profile
               upgrade_item_id: ID предмета усиления
            Returns:
                BuyItemUseCaseDict:
                    - status_code (int): HTTP статус-код.
                    - success (bool): флаг успеха покупки
                    - success_message (str | None):
                    - error_message (str | None): сообщение об ошибке
            Note:
                - 303: успешное получение данных.
                - 400: пользователь не авторизован ил не хватает денег
                - 404: не найдена книга
                - 500: непредвиденная ошибка
        """

        answer_data = {'status_code': None,
                       'error_message': None,
                       'success': None,
                       'success_message': None
                       }

        if current_user is None:
            answer_data['success'] = False
            answer_data['status_code'] = 400
            answer_data['error_message'] = f'Вы должны быть авторизованы'
            return answer_data

        try:
            await buy_upgrade_item(session_db=self.session_db,
                                   upgrade_item_id=upgrade_item_id,
                                   user=current_user)

            answer_data['status_code'] = 303
            answer_data['success'] = True
            answer_data['success_message'] = f'Вы успешно купили предмет усиления'
            await self.session_db.commit()

        except (InsufficientFundsUserError, ExpItemNotFoundError,) as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в BuyUpgradeItemUseCase: {error}', exc_info=True)

        return answer_data




