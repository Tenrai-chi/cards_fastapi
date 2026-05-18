import logging
from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.config.exceptions import NotEnoughSlotsError
from cards_app.services.cards import generate_card_start_event, create_record_in_history_receiving_card
from cards_app.services.events import get_total_news_count, get_paginated_news, get_info_start_event_awards, \
    get_info_award, update_profile_event_award_received
from cards_app.schemas.news import NewsRecordDTO, NewsDTO
from cards_app.schemas.start_event import StartEventAwardDTO, StartEventAwardsDTO
from cards_app.models import User
from cards_app.services.inventory import add_experience_book, can_user_receive_amulet, give_amulet_to_user
from cards_app.services.events import can_get_start_event_award
from cards_app.services.profile import check_can_user_receive_card, add_user_gold, create_transaction

logger = logging.getLogger(__name__)


class ProcessFightUseCase:
    """ Use case для рейтингового боя между двумя игроками
        с использованием избранных карт.
        Запускает сервисы:
            - Проверка возможности битвы.
            - Ход и результат битвы.
            - Начисление награды (золото) за участие в битве.
            - Начисление опыта карте пользователя.
            - Обновление статистики побед и поражений у обоих пользователей.
            - Начисление очков гильдии пользователю
            - Начисление награды за бой (выпадение лута)
        Создает запись в FightHistory о прошедшем бое.
    """
    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    # todo что возвращает
    async def execute(self, attacker_id: int, protector_id: int):
        pass