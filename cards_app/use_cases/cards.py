from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.config.exceptions import *
from cards_app.services.cards import (get_card_with_details, get_drop_chance_card, generate_random_card,
                                      create_record_in_history_receiving_card, get_temp_card_in_store,
                                      create_new_card_from_template)
from cards_app.schemas.cards import AmuletDTO, CardInfoDTO, CardDTO, GetFreeCardDTO, RarityCard, ClassCard
from cards_app.services.profile import (update_user_receiving_timer, check_can_user_receive_card, charge_user_gold,
                                        create_transaction)
from cards_app.utils.common import calculate_need_exp, calculate_final_price, time_difference_check
from cards_app.models.users import User


class ViewCardUseCase:
    """ Use case для просмотра карты.
        Преобразовывает данные для вывода информации о карте
        Если карты нет, то выбрасывает CardNotFoundError
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      card_id: int,
                      current_user: User
                      ) -> CardInfoDTO:

        card = await get_card_with_details(session_db=self.session_db,
                                           card_id=card_id)
        if not card:
            raise CardNotFoundError()

        need_exp = calculate_need_exp(level=card.level)
        amulet_dto = None
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

        return CardInfoDTO(card=card_dto,
                           amulet=amulet_dto,
                           is_owner=is_owner
                           )


class ViewGetFreeCard:
    """ Use case для просмотра страницы с получением бесплатной карты """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user: User) -> GetFreeCardDTO:
        data_for_page: dict = await get_drop_chance_card(session_db=self.session_db)
        all_classes = data_for_page['classes']
        all_rarities = data_for_page['rarities']

        classes_card = []
        rarities_card = []
        for class_card in all_classes:
            classes_card.append(ClassCard(name=class_card.name,
                                          skill_description=class_card.description))

        for rarity_card in all_rarities:
            rarities_card.append(RarityCard(name=rarity_card.name,
                                            chance_drop=rarity_card.drop_chance))
        can_get_card = False
        if current_user and current_user.profile.receiving_timer is not None:
            hours_for_get_free_card = 6
            check_time, _ = time_difference_check(current_user.profile.receiving_timer, hours_for_get_free_card)
            if check_time:
                can_get_card = True
        elif current_user:
            can_get_card = True
        else:
            can_get_card = False
        return GetFreeCardDTO(all_classes=classes_card,
                              all_rarities=rarities_card,
                              can_get_free_card=can_get_card)


class GetFreeCardUseCase:
    """ Use case для получения случайной бесплатной карты """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      current_user: User
                      ) -> dict:

        hours_for_get_free_card = 6
        answer_data = {'new_card_id': None,
                       'error_message': None}

        if current_user is None:
            answer_data['error_message'] = f'Для получения бесплатной карты нужно быть авторизованным'
            return answer_data

        if current_user.profile.receiving_timer is not None:
            check_time, hours = time_difference_check(check_time=current_user.profile.receiving_timer,
                                                      need_hours=hours_for_get_free_card)
            if not check_time:
                answer_data['error_message'] = f'Для получения бесплатной карты осталось: {hours_for_get_free_card - hours}'
                return answer_data

        try:
            await check_can_user_receive_card(session_db=self.session_db,
                                              current_user=current_user,
                                              need_slots=1)
            await update_user_receiving_timer(session_db=self.session_db,
                                              current_user=current_user)
            new_card_id = await generate_random_card(session_db=self.session_db,
                                                     owner_id=current_user.profile.id)
            await create_record_in_history_receiving_card(session_db=self.session_db,
                                                          card_id=new_card_id,
                                                          user_id=current_user.profile.id,
                                                          method_receiving='Генерация')
            answer_data['new_card_id'] = new_card_id
            await self.session_db.commit()

        except NotEnoughSlotsError as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = str(error)

        except Exception as error:
            await self.session_db.rollback()
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {error}'

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
                       'new_card_id': int}

        # Проверка, что пользователь авторизован
        if current_user is None:
            answer_data['success'] = False
            answer_data['error_message'] = f'Для получения бесплатной карты нужно быть авторизованным'
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
            await self.session_db.commit()

        except (NotEnoughSlotsError, InsufficientFundsUserError, CardNotOnSaleError, CardInStoreNotFoundError) as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = str(error)

        except Exception as error:
            answer_data['success'] = False
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'

        return answer_data
