from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.config.exceptions import (InsufficientFundsUserError, NotEnoughSlotsError, CardNotOnSaleError,
                                         CardInStoreNotFoundError)
from cards_app.models import User
from cards_app.schemas.store import CardInStoreDTO, CardStoreDTO
from cards_app.services.cards import (get_temp_card_in_store, create_new_card_from_template,
                                      create_record_in_history_receiving_card)
from cards_app.services.profile import check_can_user_receive_card, charge_user_gold, create_transaction
from cards_app.services.store import get_cards_in_store
from cards_app.utils.common import calculate_final_price


class ViewCardStoreUseCase:
    """ Use case для просмотра магазина карт.
        Преобразовывает данные для вывода информации о продаваемых картах.
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self) -> dict:
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
                      current_user: User,
                      temp_card_id: int,
                      ) -> dict:

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
                                     user_id=current_user.id,
                                     gold_before=gold_transaction['gold_before'],
                                     gold_after=gold_transaction['gold_after'],
                                     comment='Покупка в магазине карт')

            # Создание записи о получении карты
            await create_record_in_history_receiving_card(session_db=self.session_db,
                                                          card_id=new_card_id,
                                                          user_id=current_user.profile.id,
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
            answer_data['success'] = False
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'
            answer_data['status_code'] = 500

        return answer_data
