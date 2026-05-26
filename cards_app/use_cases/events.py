import logging

from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.exeptions import NotEnoughSlotsError
from cards_app.services.cards import generate_card_start_event, create_record_in_history_receiving_card
from cards_app.services.events import (get_total_news_count, get_paginated_news, get_info_start_event_awards,
                                       get_info_award, update_profile_event_award_received)
from cards_app.schemas.news import NewsRecordDTO, NewsDTO
from cards_app.schemas.start_event import StartEventAwardDTO, StartEventAwardsDTO
from cards_app.types import ViewNewsUseCaseDict, ViewStartEventUseCaseDict, GetAwardStartEventUseCaseDict
from cards_app.models import User
from cards_app.services.inventory import add_experience_book, can_user_receive_amulet, give_amulet_to_user
from cards_app.services.events import can_get_start_event_award
from cards_app.services.profile import check_can_user_receive_card, add_user_gold, create_transaction

logger = logging.getLogger(__name__)


class ViewNewsUseCase:
    """ Use case для просмотра новостей.
        Преобразует список новостей в DTO с информацией о страницах.
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, page: int, size: int
                      ) -> ViewNewsUseCaseDict:
        """ Выполняет получение новостей и формирует DTO для отображения.
            Args:
                page: номер страницы (начиная с 1).
                size: количество новостей на странице.
            Returns:
                ViewNewsUseCaseDict:
                    - news_dto (NewsDTO): DTO с новостями и пагинацией.
                    - status_code (int):  HTTP статус-код всегда 200
        """

        answer_data = {'news_dto': None,
                       'status_code': None}

        offset = (page - 1) * size
        news_models = await get_paginated_news(self.session_db, limit=size, offset=offset)

        total = await get_total_news_count(self.session_db)
        total_pages = (total + size - 1) // size

        news_records = [
            NewsRecordDTO(title=item.title,
                          theme=item.theme,
                          text=item.text,
                          date_and_time=item.date_time_create
                          )
            for item in news_models
        ]

        news_dto = NewsDTO(items=news_records,
                           total=total,
                           page=page,
                           size=size,
                           total_pages=total_pages
                           )
        answer_data['status_code'] = 200
        answer_data['news_dto'] = news_dto
        return answer_data


class ViewStartEventUseCase:
    """ Use case для просмотра страницы стартового события.
        Доступен только для авторизованных пользователей?
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user: User | None
                      ) -> ViewStartEventUseCaseDict:
        """ Выполняет получение списка наград стартового события и формирует DTO для отображения.
            Args:
                current_user: User + Profile текущего пользователя
            Returns:
                ViewStartEventUseCaseDict:
                    - start_event_awards_dto (StartEventAwardsDTO | None): DTO с новостями и пагинацией (если пользователь авторизован).
                    - status_code (int):  HTTP статус-код, всегда 200
        """

        answer_data = {'start_event_awards_dto': None,
                       'status_code': None}

        start_event_awards = await get_info_start_event_awards(session_db=self.session_db)
        awards = [StartEventAwardDTO(day=award.day_event_visit,
                                     type_award=award.type_award,
                                     amount_or_rarity=award.amount_or_rarity_award,
                                     description=award.description
                                     )
                  for award in start_event_awards
                  ]
        if current_user is None:
            can_get = False
            received = 0
        else:
            can_get = await can_get_start_event_award(user=current_user)
            received = current_user.profile.event_visit

        start_event_awards_dto = StartEventAwardsDTO(awards=awards,
                                                     can_get_award=can_get,
                                                     received=received)

        answer_data['start_event_awards_dto'] = start_event_awards_dto
        answer_data['status_code'] = 200

        return answer_data


class GetAwardStartEventUseCase:
    """ Use case для получения награды в стартовом событии """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user: User | None
                      ) -> GetAwardStartEventUseCaseDict:
        """ Выполняет получение награды в стартовом событии.
           Args:
               current_user: User + Profile текущего пользователя

           Returns:
               GetAwardStartEventUseCaseDict:
                   - success_message (str | None): при удачном получении награды, кроме карты
                   - error_message (str | None): сообщение об ошибке.
                   - new_card_id (int | None): ID созданной карты, если награда была картой
                   - status_code (int): HTTP статус-код.
           Note:
               - 303: успешное получение (перенаправление на просмотр карты или на ту же страницу).
               - 400: ошибка доступа (пользователь не авторизован, либо он не может получить награду)
               - 500: непредвиденная ошибка.
           """

        answer_data = {'success_message': None,
                       'error_message': None,
                       'new_card_id': None,
                       'status_code': None}

        # Проверка, что пользователь авторизован
        if current_user is None:
            answer_data['error_message'] = f'Для получения награды вы должны быть авторизованы'
            answer_data['status_code'] = 400
            return answer_data

        # Проверка, что пользователь может получить награду
        if not await can_get_start_event_award(user=current_user):
            answer_data['error_message'] = f'Вы не можете получить награду стартового события'
            answer_data['status_code'] = 400
            return answer_data

        try:
            # Получение информации о награде дня
            day_visit = (current_user.profile.event_visit or 0) + 1
            award_of_day = await get_info_award(session_db=self.session_db,
                                                day_visit=day_visit)

            books = ['Маленькая книга опыта', 'Средняя книга опыта', 'Большая книга опыта']
            if award_of_day.type_award in books:
                await add_experience_book(session_db=self.session_db,
                                          user_profile_id=current_user.profile.id,
                                          amount=int(award_of_day.amount_or_rarity_award),
                                          name_book=award_of_day.type_award)
                answer_data['success_message'] = (f'Вы получили в награду {award_of_day.type_award} '
                                                  f'{award_of_day.amount_or_rarity_award} шт.')
                answer_data['status_code'] = 303

            elif award_of_day.type_award == 'Амулет':
                await can_user_receive_amulet(session_db=self.session_db,
                                              current_user=current_user,
                                              need_slots=1)
                await give_amulet_to_user(session_db=self.session_db,
                                          owner_id=current_user.profile.id,
                                          name_amulet=award_of_day.amount_or_rarity_award)
                answer_data['success_message'] = (f'Вы получили в награду {award_of_day.type_award} '
                                                  f'"{award_of_day.amount_or_rarity_award}"')
                answer_data['status_code'] = 303

            elif award_of_day.type_award == 'Золото':
                data_for_transaction: dict = await add_user_gold(session_db=self.session_db,
                                                                 current_user=current_user,
                                                                 add_gold=int(award_of_day.amount_or_rarity_award))
                await create_transaction(session_db=self.session_db,
                                         user_profile_id=current_user.profile.id,
                                         gold_before=data_for_transaction['gold_before'],
                                         gold_after=data_for_transaction['gold_after'],
                                         comment=f'Получение награды в боевом событии')
                answer_data['success_message'] = f'Вы получили в награду {award_of_day.amount_or_rarity_award} золота'
                answer_data['status_code'] = 303

            elif award_of_day.type_award == 'Карта':
                await check_can_user_receive_card(session_db=self.session_db,
                                                  current_user=current_user,
                                                  need_slots=1)
                new_card_id = await generate_card_start_event(session_db=self.session_db,
                                                              user_profile_id=current_user.profile.id,
                                                              rarity_name=award_of_day.amount_or_rarity_award)
                await create_record_in_history_receiving_card(session_db=self.session_db,
                                                              card_id=new_card_id,
                                                              user_profile_id=current_user.profile.id,
                                                              method_receiving='Стартовое событие')
                answer_data['status_code'] = 303
                answer_data['new_card_id'] = new_card_id
            await update_profile_event_award_received(session_db=self.session_db, user=current_user)
            await self.session_db.commit()

        except NotEnoughSlotsError as error:
            await self.session_db.rollback()
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            await self.session_db.rollback()
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в GetAwardStartEventUseCase: {error}', exc_info=True)

        return answer_data
