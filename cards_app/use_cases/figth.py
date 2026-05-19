import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.config.exceptions import NotEnoughSlotsError, UserNotFoundError, NoCurrentCardError, \
    CooldownNotElapsedError
from cards_app.services.cards import generate_card_start_event, create_record_in_history_receiving_card
from cards_app.services.events import get_total_news_count, get_paginated_news, get_info_start_event_awards, \
    get_info_award, update_profile_event_award_received
from cards_app.schemas.fight import Participant, FightDTO
from cards_app.schemas.start_event import StartEventAwardDTO, StartEventAwardsDTO
from cards_app.models import User
from cards_app.services.fight import validate_battle_preconditions, check_last_fight, get_cards_participants, \
    stats_calculation, fight_now
from cards_app.services.inventory import add_experience_book, can_user_receive_amulet, give_amulet_to_user
from cards_app.services.events import can_get_start_event_award
from cards_app.services.profile import check_can_user_receive_card, add_user_gold, create_transaction

logger = logging.getLogger(__name__)


class ProcessFightUseCase:
    """ Use case для рейтингового боя между двумя игроками
        с использованием избранных карт.
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, user: User | None, enemy_id: int) -> dict[str, Any]:
        """ Оркестрирует процесс рейтинговой битвы.
            1. Проверяет возможность битвы
            2. Проводит битву между 2 картами
            3. Начисляет золото и опыт и награды, обновляет статистику пользователей
            4. Создает запись в FightHistory
            Args:
                user (User | None): объект текущего пользователя (User) с подгруженным профилем
                enemy_id (int | None): ID противника
            Returns:
                dict
                    - status_code: чета там
                    - error_message: ошибка
                    - fight_dto: DTO
            Note:
                - 303: успешная битва (перенаправление на итог битвы)
                - 400: ошибка доступа (не выполнены условия, либо пользователь не авторизован)
                - 500: непредвиденная ошибка.
        """

        answer_data = {'fight_dto': None,
                       'error_message': None,
                       'status_code': None}

        if user is None:
            answer_data['error_message'] = f'Для участия в битве вы должны быть авторизованы'
            answer_data['status_code'] = 400
            return answer_data
        try:
            # 1. Проверка, что бой может состояться
            participants: dict = await validate_battle_preconditions(self.session_db,
                                                                     attacker_id=user.id,
                                                                     protector_id=enemy_id)
            user = participants.get('attacker')
            enemy = participants.get('protector')

            # 2. Подготовка карт и характеристик
            cards: dict = await get_cards_participants(session_db=self.session_db,
                                                       attacker_card_id=user.profile.current_card_id,
                                                       protector_card_id=enemy.profile.current_card_id)
            user_card = cards.get('attacker_card')
            enemy_card = cards.get('protector_card')

            # 3. Бой между участниками
            data_fight: dict = await fight_now(user_card=user_card,
                                               enemy_card=enemy_card)
            is_victory = data_fight.get('is_victory')
            history_fight = data_fight.get('history_fight')
            winner = data_fight.get('winner')
            loser = data_fight.get('loser')

            # 4. Изменение статистики win\lose
            # 5. Увеличение характеристик карты пользователя
            # 6. Начисление золота и очков гильдии в зависимости от исхода битвы пользователю
            # 7. Выпадение предметов после боя
            # 8. Создание записи о бое в истории



            answer_data['fight_dto'] = 'Приветики'

        except (UserNotFoundError, NoCurrentCardError, CooldownNotElapsedError) as error:
            await self.session_db.rollback()
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            await self.session_db.rollback()
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в GetAwardStartEventUseCase: {error}', exc_info=True)
        return answer_data
