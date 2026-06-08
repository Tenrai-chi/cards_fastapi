import logging

from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.exeptions import UserFavoriteException
from cards_app.services.profile import (get_base_info_profile, get_battle_stats,
                                        get_user_fight_history, is_favorite, add_user_to_favorite,
                                        remove_user_from_favorite, ensure_favorite_slot_available, get_favorite_user,
                                        get_rating_users, get_total_users_count, get_user_transactions)
from cards_app.services.cards import get_card_with_details
from cards_app.schemas.profile import (ProfileResponseDTO, ProfileBaseDTO, GuildDTO,
                                       CardDTO, AmuletDTO, FightHistoryRecordDTO, CardBriefDTO, FavoriteUserDTO,
                                       FavoriteUsersPageDTO, UserRatingTableDTO, RatingTableDTO, TransactionsDTO,
                                       RecordTransaction)
from cards_app.models.users import User
from cards_app.exeptions import UserNotFoundError, NotEnoughSlotsError
from cards_app.types import (ViewProfileUseCaseDict, AddFavoriteUserUseCaseDict, RemoveFavoriteUserUseCaseDict,
                             FavoriteUsersUseCaseDict, ViewUsersRatingDict, UserTransactionsUseCaseDict)

logger = logging.getLogger(__name__)


class ViewProfileUseCase:
    """ Use case для просмотра профиля пользователя.
        Координирует получение данных профиля в зависимости от того, кто просматривает профиль.
        Возможны 3 случая: аноним, гость, хозяин
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      current_user: User | None,
                      target_user_id: int
                      ) -> ViewProfileUseCaseDict:
        """ Выполняет получение и подготовку данных профиля для отображения
            Args:
                current_user: User + Profile текущего пользователя
                target_user_id: ID Profile пользователя, чей профиль просматривается

            Returns:
                ViewProfileUseCaseDict:
                    - user_info (ProfileResponseDTO | None): DTO с полной информацией профиля
                    - error_message (str | None): сообщение об ошибке
                    - status_code (int): HTTP статус-код
            Note:
                - 200: успешное получение данных
                - 404: пользователь не найден
                - 500: непредвиденная ошибка
        """

        answer_data = {'user_info': None,
                       'error_message': None,
                       'status_code': None}

        try:
            # Для просмотра своей страницы все равно вызывается загрузка профиля, так как нужна еще и гильдия
            target_user = await get_base_info_profile(session_db=self.session_db,
                                                      user_id=target_user_id)
        except UserNotFoundError as error:
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code
            return answer_data
        except Exception as error:
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в ViewProfileUseCase: {error}', exc_info=True)
            return answer_data

        base_dto = ProfileBaseDTO(id=target_user.id,
                                  username=target_user.username,
                                  about_user=target_user.profile.about_user,
                                  profile_pic=target_user.profile.profile_pic,
                                  win=target_user.profile.win,
                                  lose=target_user.profile.lose,
                                  rating=target_user.profile.rating
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
            card = await get_card_with_details(session_db=self.session_db,
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
            fights = await get_user_fight_history(session_db=self.session_db,
                                                  profile_id=target_user.profile.id,
                                                  limit=50)
            battle_history = []
            for fight in fights:

                target_is_participant1 = (fight.participant1_id == target_user.profile.id)

                opponent_profile = fight.participant2 if target_is_participant1 else fight.participant1

                # Карты: у participant1 – fight.card1, у participant2 – fight.card2
                target_card = fight.card1 if target_is_participant1 else fight.card2
                opponent_card = fight.card2 if target_is_participant1 else fight.card1

                # Определяем результат
                if fight.winner_id is None:
                    result = 'draw'
                elif fight.winner_id == target_user.profile.id:
                    result = 'win'
                else:
                    result = 'loss'

                # Получаем данные оппонента (пользователь из профиля)
                opponent_user = opponent_profile.user

                battle_history.append(FightHistoryRecordDTO(date_and_time=fight.date_and_time,
                                                            result=result,
                                                            user_card=CardBriefDTO(
                                                                id=target_card.id,
                                                                class_name=target_card.class_card.name,
                                                                type_name=target_card.type_card.name
                                                            ),
                                                            opponent_id=opponent_user.id,
                                                            opponent_username=opponent_user.username,
                                                            opponent_card=CardBriefDTO(
                                                                id=opponent_card.id,
                                                                class_name=opponent_card.class_card.name,
                                                                type_name=opponent_card.type_card.name
                                                            )
                                                            )
                                      )

        elif current_user is not None:
            role = 'guest'
            if current_user.profile:
                stats = await get_battle_stats(session_db=self.session_db,
                                               profile1_id=current_user.profile.id,
                                               profile2_id=target_user.profile.id
                                               )
                win_vs, lose_vs = stats
                is_fav = await is_favorite(session_db=self.session_db,
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
                                       role=role,
                                       )
        answer_data['user_info'] = user_info
        answer_data['status_code'] = 200
        return answer_data


class AddFavoriteUserUseCase:
    """ Use case для добавления пользователя в список избранных """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      current_user: User | None,
                      target_user_id: int
                      ) -> AddFavoriteUserUseCaseDict:
        """ Добавляет целевого пользователя в избранное текущего.
            Args:
                current_user: User + Profile текущего пользователя
                target_user_id: ID Profile пользователя, которого нужно добавить в избранное.
            Returns:
                AddFavoriteUserUseCaseDict:
                    - success (bool): True при успешном добавлении.
                    - error_message (str | None): сообщение об ошибке.
                    - status_code (int): HTTP статус-код.
                    - success_message (str | None): сообщение об успехе.
            Note:
                - 303: успешное добавление и перенаправление
                - 400: ошибка доступа
                - 500: непредвиденная ошибка
        """

        answer_data = {'success': None,
                       'error_message': None,
                       'status_code': None,
                       'success_message': None}

        if current_user is None:
            answer_data['success'] = False
            answer_data['error_message'] = 'Для данного действия необходимо авторизоваться'
            answer_data['status_code'] = 400
            return answer_data

        try:
            await ensure_favorite_slot_available(self.session_db, current_user)
            await add_user_to_favorite(session_db=self.session_db,
                                       current_user_id=current_user.profile.id,
                                       target_user_id=target_user_id)

            await self.session_db.commit()
            answer_data['success'] = True
            answer_data['status_code'] = 303
            answer_data['success_message'] = 'Пользователь добавлен в избранное'
            return answer_data

        except (UserFavoriteException, NotEnoughSlotsError) as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

            return answer_data

        except Exception as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в AddFavoriteUserUseCase: {error}', exc_info=True)

            return answer_data


class RemoveFavoriteUserUseCase:
    """ Use case для удаления пользователя из списка избранных """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      current_user: User | None,
                      target_user_id: int
                      ) -> RemoveFavoriteUserUseCaseDict:
        """ Удаляет целевого пользователя из избранного текущего.
            Args:
                current_user: User + Profile текущего пользователя
                target_user_id: ID Profile пользователя, которого нужно удалить из избранного.
            Returns:
                RemoveFavoriteUserUseCaseDict:
                    - success (bool): True при успешном удалении.
                    - error_message (str | None): сообщение об ошибке.
                    - status_code (int): HTTP статус-код.
                    - success_message (str | None): сообщение об успехе.
            Note:
                - 303: успешное удаление и перенаправление
                - 400: ошибка доступа
                - 500: непредвиденная ошибка
        """

        answer_data = {'success': None,
                       'error_message': None,
                       'status_code': None,
                       'success_message': None}

        if current_user is None:
            answer_data['success'] = False
            answer_data['error_message'] = 'Для данного действия необходимо авторизоваться'
            answer_data['status_code'] = 400
            return answer_data

        try:
            await remove_user_from_favorite(session_db=self.session_db,
                                            current_user_id=current_user.profile.id,
                                            target_user_id=target_user_id)

            await self.session_db.commit()
            answer_data['success'] = True
            answer_data['status_code'] = 303
            answer_data['success_message'] = 'Пользователь удален из избранного'
            return answer_data

        except (UserNotFoundError, UserFavoriteException) as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = str(error)
            answer_data['status_code'] = error.status_code

            return answer_data

        except Exception as error:
            await self.session_db.rollback()
            answer_data['success'] = False
            answer_data['error_message'] = f'Произошла непредвиденная ошибка: {str(error)}'
            answer_data['status_code'] = 500
            logger.error(f'Непредвиденная ошибка в RemoveFavoriteUserUseCase: {error}', exc_info=True)

            return answer_data


class FavoriteUsersUseCase:
    """ Use case для просмотра списка избранных """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user: User | None,
                      ) -> FavoriteUsersUseCaseDict:
        """ Формирует FavoriteUsersPageDTO для просмотра списка избранных пользователей
            Args:
                current_user: User + Profile текущего пользователя
            Returns:
                FavoriteUsersUseCaseDict:
                    - favorite_users_dto (FavoriteUsersPageDTO | None): DTO избранных пользователей
                    - error_message (str | None): сообщение об ошибке.
                    - status_code (int): HTTP статус-код.
            Note:
                - 200: успешное получение данных
        """

        answer_data = {'favorite_users_dto': None,
                       'status_code': None,
                       'error_message': None}

        if current_user is None:
            answer_data['error_message'] = f'Вы должны быть авторизованы'
            answer_data['status_code'] = 404
            return answer_data
        all_favorite_users: list = await get_favorite_user(self.session_db,
                                                           user_profile_id=current_user.profile.id)
        favorite_users = []
        for user in all_favorite_users:
            favorite_users.append(FavoriteUserDTO(id=user.favorite_user.id,
                                                  username=user.favorite_user.user.username))
        favorite_users_dto = FavoriteUsersPageDTO(amount_users=len(all_favorite_users),
                                                  max_amount_users=current_user.profile.max_favorite,
                                                  favorite_users=favorite_users)
        answer_data['status_code'] = 200
        answer_data['favorite_users_dto'] = favorite_users_dto

        return answer_data


class ViewUsersRatingUseCase:
    """ Use Case для просмотра таблицы рейтинга """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, page: int, size: int
                      ) -> ViewUsersRatingDict:
        """ Выполняет получение новостей и формирует DTO для отображения.
            Args:
                page: номер страницы (начиная с 1).
                size: количество новостей на странице.
            Returns:
                ViewUsersRatingDict:
                    - rating_dto (RatingTableDTO | None): DTO с пользователя и пагинацией.
                    - status_code (int):  HTTP статус-код всегда 200
        """

        answer_data = {'rating_dto': None,
                       'status_code': None}

        offset = (page - 1) * size
        users_models = await get_rating_users(session_db=self.session_db, limit=size, offset=offset)

        total = await get_total_users_count(self.session_db)
        total_pages = (total + size - 1) // size

        user_record = [UserRatingTableDTO(id=user.id,
                                          username=user.username,
                                          rating=user.profile.rating)
                       for user in users_models
                       ]

        rating_dto = RatingTableDTO(user_rating=user_record,
                                    total=total,
                                    page=page,
                                    size=size,
                                    total_pages=total_pages)
        answer_data['rating_dto'] = rating_dto
        answer_data['status_code'] = 200
        return answer_data


class UserTransactionsUseCase:
    """ Use case для просмотра транзакций """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user: User | None,
                      ) -> UserTransactionsUseCaseDict:
        """ Формирует TransactionsDTO пользователя
            Args:
                current_user: User + Profile текущего пользователя
            Returns:
                UserTransactionsUseCaseDict:
                    - transactions (TransactionsDTO | None): DTO избранных пользователей
                    - status_code (int): HTTP статус-код.
                    - error_message: текст ошибки
            Note:
                - 200: успешное получение данных
                - 400: если пользователь не авторизован
        """

        answer_data = {'transactions_dto': None,
                       'error_message': None,
                       'status_code': None}

        if current_user is None:
            answer_data['error_message'] = f'Для просмотра транзакций необходимо быть авторизован'
            answer_data['status_code'] = 400
            return answer_data

        user_transactions: list = await get_user_transactions(session_db=self.session_db,
                                                              user_id=current_user.id)
        user_transactions_dto = TransactionsDTO(
            transactions=[
                RecordTransaction(date_and_time=tx.date_and_time,
                                  before=tx.before,
                                  after=tx.after,
                                  comment=tx.comment,
                                  delta=tx.after - tx.before
                                  )
                for tx in user_transactions
            ],
        )

        answer_data['transactions_dto'] = user_transactions_dto
        answer_data['status_code'] = 200
        return answer_data
