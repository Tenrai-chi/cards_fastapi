import logging

from sqlalchemy.ext.asyncio import AsyncSession
from cards_app.exeptions import UserNotFoundError, NoCurrentCardError, CooldownNotElapsedError
from cards_app.models import User
from cards_app.schemas import FightDTO, Participant
from cards_app.services.cards import update_card_experience
from cards_app.services.fight import (validate_battle_preconditions, get_cards_participants, fight_now,
                                      create_record_fight_history)
from cards_app.services.guild import update_guild_points_user
from cards_app.services.inventory import reward_loot_after_fight
from cards_app.services.profile import update_win_lose, add_gold_for_fight, create_transaction, update_rating_user
from cards_app.types import ProcessFightUseCaseDict, AddGoldForFightDict, RewardLootAfterFightDict

logger = logging.getLogger(__name__)


class ProcessFightUseCase:
    """ Use case для рейтингового боя между двумя игроками
        с использованием избранных карт.
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, user: User | None, enemy_id: int
                      ) -> ProcessFightUseCaseDict:
        """ Оркестрирует процесс рейтинговой битвы.
            1. Проверяет возможность битвы
            2. Проводит битву между 2 картами
            3. Начисляет золото и опыт и награды, обновляет статистику пользователей
            4. Создает запись в FightHistory
            Args:
                user: объект текущего пользователя (User) с подгруженным профилем
                enemy_id: ID User противника
            Returns:
                ProcessFightUseCaseDict
                    - fight_dto (FightDTO | None): DTO с результатом битвы
                    - error_message (str | None): сообщение об ошибке
                    - status_code (int): HTTP статус-код.

            Note:
                - 200: успешная битва (перенаправление на итог битвы)
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
                                                                     user_id=user.id,
                                                                     enemy_id=enemy_id)
            user = participants.get('user')
            enemy = participants.get('enemy')

            # 2. Подготовка карт и характеристик
            cards: dict = await get_cards_participants(session_db=self.session_db,
                                                       user_card_id=user.profile.current_card_id,
                                                       enemy_card_id=enemy.profile.current_card_id)
            user_card = cards.get('user_card')
            enemy_card = cards.get('enemy_card')

            # 3. Бой между участниками
            data_fight: dict = await fight_now(user=user,
                                               enemy=enemy,
                                               user_card=user_card,
                                               enemy_card=enemy_card)
            is_victory = data_fight.get('is_victory')
            history_fight = data_fight.get('history_fight')
            winner = data_fight.get('winner')
            loser = data_fight.get('loser')

            # 4. Изменение статистики win\lose
            if is_victory:
                await update_win_lose(session_db=self.session_db,
                                      winner=winner,
                                      loser=loser)

            # 5. Получение опыта карт
            for card in (user_card, enemy_card):
                await update_card_experience(session_db=self.session_db,
                                             card=card)

            # 6. Определение результатов
            if not is_victory:
                user_result = enemy_result = 'draw'
            else:
                user_result, enemy_result = ('win', 'lose') if winner.id == user.id else ('lose', 'win')

            # 7. Начисление золота
            user_gold_data: AddGoldForFightDict = await add_gold_for_fight(session_db=self.session_db,
                                                                           user=user,
                                                                           result_battle=user_result)
            enemy_gold_data: AddGoldForFightDict = await add_gold_for_fight(session_db=self.session_db,
                                                                            user=enemy,
                                                                            result_battle=enemy_result)

            # 8. Обновление рейтинга и очков гильдии
            await update_guild_points_user(session_db=self.session_db,
                                           user=user,
                                           result_battle=user_result)
            await update_guild_points_user(session_db=self.session_db,
                                           user=enemy,
                                           result_battle=enemy_result)
            await update_rating_user(session_db=self.session_db, user=user, user_fight_result=user_result)
            await update_rating_user(session_db=self.session_db, user=enemy, user_fight_result=enemy_result)

            # 9. Создание транзакций у пользователей
            await create_transaction(session_db=self.session_db,
                                     user_profile_id=user.profile.id,
                                     gold_before=user_gold_data.get('gold_before'),
                                     gold_after=user_gold_data.get('gold_after'),
                                     comment=user_gold_data.get('comment'))
            await create_transaction(session_db=self.session_db,
                                     user_profile_id=user.profile.id,
                                     gold_before=enemy_gold_data.get('gold_before'),
                                     gold_after=enemy_gold_data.get('gold_after'),
                                     comment=enemy_gold_data.get('comment'))
            # 10. Выпадение наград для пользователя после боя
            user_buff_elf_value = user_card.class_card.numeric_value if user_card.class_card.name == 'Эльф' else 0
            user_loot: RewardLootAfterFightDict = await reward_loot_after_fight(session_db=self.session_db,
                                                                                user=user,
                                                                                buff_value=user_buff_elf_value)

            # Выпадение наград для соперника после боя (не выводится на странице)
            enemy_buff_elf_value = enemy_card.class_card.numeric_value if enemy_card.class_card.name == 'Эльф' else 0
            await reward_loot_after_fight(session_db=self.session_db,
                                          user=enemy,
                                          buff_value=enemy_buff_elf_value)
            # 11. Создание записи о бое в истории
            await create_record_fight_history(session_db=self.session_db,
                                              is_victory=is_victory,
                                              participant1_id=user.profile.id,
                                              participant2_id=enemy.profile.id,
                                              card1_id=user_card.id,
                                              card2_id=enemy_card.id,
                                              winner_id=winner.profile.id if is_victory else None)

            user_dto = Participant(id=user.id,
                                   username=user.username,
                                   profile_pic=user.profile.profile_pic)
            enemy_dto = Participant(id=enemy.id,
                                    username=enemy.username,
                                    profile_pic=enemy.profile.profile_pic)

            answer_data['fight_dto'] = FightDTO(user=user_dto,
                                                enemy=enemy_dto,
                                                history_fight=history_fight,
                                                is_victory=is_victory,
                                                reward_item_user=user_loot.get('exp_items'),
                                                reward_amulet_user=user_loot.get('amulets'),
                                                winner_id=winner.id if is_victory else None)
            answer_data['status_code'] = 200
            await self.session_db.commit()

        except (UserNotFoundError, NoCurrentCardError, CooldownNotElapsedError) as error:
            await self.session_db.rollback()
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

        except Exception as error:
            await self.session_db.rollback()
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в ProcessFightUseCase: {error}', exc_info=True)
        return answer_data
