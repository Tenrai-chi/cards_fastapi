from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.services.profile import (get_base_info_profile, get_battle_stats,
                                        get_fight_history_user, is_favorite)
from cards_app.services.cards import get_card_with_details
from cards_app.schemas.profile import (ProfileResponseDTO, ProfileBaseDTO, GuildDTO,
                                       CardDTO, AmuletDTO, FightHistoryRecordDTO, CardBriefDTO
                                       )
from cards_app.models.users import User
from cards_app.config.exceptions import UserNotFoundError


class ViewProfileUseCase:
    """ Use case для просмотра профиля пользователя.
        Координирует получение данных профиля в зависимости от того, кто просматривает профиль.
        Возможны 3 случая: аноним, гость, хозяин
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self,
                      current_user: Optional[User],
                      target_user_id: int
                      ) -> dict:

        answer_data = {'user_info': None,
                       'error_message': None}

        try:
            target_user = await get_base_info_profile(session_db=self.session,
                                                      user_id=target_user_id)
        except UserNotFoundError as error:
            answer_data['error_message'] = str(error)
            return answer_data

        base_dto = ProfileBaseDTO(about_user=target_user.profile.about_user,
                                  profile_pic=target_user.profile.profile_pic,
                                  win=target_user.profile.win,
                                  lose=target_user.profile.lose,
                                  )

        guild_dto = None
        if target_user.profile.guild:
            guild_dto = GuildDTO(id=target_user.profile.guild.id,
                                 name=target_user.profile.guild.name,
                                 )

        # 4. Избранная карта и амулет
        card_dto = None
        amulet_dto = None
        if target_user.profile.current_card_id:
            card = await get_card_with_details(session_db=self.session,
                                               card_id=target_user.profile.current_card_id)
            if card:
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
                                   )
                if card.amulet:
                    amulet_dto = AmuletDTO(id=card.amulet.id,
                                           name=card.amulet.amulet_type.name,
                                           bonus_hp=card.amulet.amulet_type.bonus_hp,
                                           bonus_damage=card.amulet.amulet_type.bonus_damage,
                                           )

        is_owner = current_user and current_user.id == target_user_id

        user_email = None
        battle_history = None
        win_vs = None
        lose_vs = None
        is_fav = None
        role = 'anonymous'

        if is_owner:
            role = 'owner'
            user_email = target_user.email
            fights = await get_fight_history_user(session_db=self.session,
                                                  profile_id=target_user.profile.id,
                                                  limit=50)
            battle_history = []
            for fight in fights:
                is_win = (fight.winner_id == target_user.profile.id)
                user_card = fight.card_winner if is_win else fight.card_loser
                opponent_card = fight.card_loser if is_win else fight.card_winner
                opponent_profile = fight.loser if is_win else fight.winner
                opponent_user = opponent_profile.user

                battle_history.append(FightHistoryRecordDTO(date_and_time=fight.date_and_time,
                                                            result='win' if is_win else 'loss',
                                                            user_card=CardBriefDTO(id=user_card.id,
                                                                                   class_name=user_card.class_card.name,
                                                                                   type_name=user_card.type_card.name,
                                                                                   ),
                                                            opponent_profile_id=opponent_profile.id,
                                                            opponent_username=opponent_user.username,
                                                            opponent_card=CardBriefDTO(id=opponent_card.id,
                                                                                       class_name=opponent_card.class_card.name,
                                                                                       type_name=opponent_card.type_card.name,
                                                                                       ),
                                                            ))

        elif current_user is not None:
            role = 'guest'
            if current_user.profile:
                stats = await get_battle_stats(session_db=self.session,
                                               profile1_id=current_user.profile.id,
                                               profile2_id=target_user.profile.id
                                               )
                win_vs, lose_vs = stats
                is_fav = await is_favorite(session_db=self.session,
                                           current_profile_id=current_user.profile.id,
                                           target_profile_id=target_user.profile.id
                                           )

        user_info = ProfileResponseDTO(profile=base_dto,
                                       guild=guild_dto,
                                       card=card_dto,
                                       amulet=amulet_dto,
                                       user_email=user_email,
                                       battle_history=battle_history,
                                       win_vs=win_vs,
                                       lose_vs=lose_vs,
                                       is_favorite=is_fav,
                                       role=role
                                       )
        answer_data['user_info'] = user_info
        return answer_data
