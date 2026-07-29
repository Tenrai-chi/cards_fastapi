import logging

from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.exeptions import UserFavoriteException
from cards_app.schemas.base import AmuletBase, GuildBase, CardBase
from cards_app.schemas.profile import (
    FavoriteUsersPageDTO, FavoriteUserDTO, RecordTransaction, TransactionsDTO,
    FightHistoryRecordDTO, ProfileFullInfoDTO
)
from cards_app.schemas.response import (
    FavoriteUsersUseCaseResponse, UserTransactionsUseCaseResponse,
    ViewProfileUseCaseResponse, ToggleFavoriteUserUseCaseResponse
)
from cards_app.services.profile import (
    get_base_info_profile, get_battle_stats,
    get_user_fight_history, is_favorite, add_user_to_favorite,
    remove_user_from_favorite, ensure_favorite_slot_available, get_favorite_user,
    get_user_transactions
)
from cards_app.services.cards import get_card_with_details
from cards_app.schemas.profile import CardDTO
from cards_app.models.users import User
from cards_app.exeptions import UserNotFoundError, NotEnoughSlotsError
from cards_app.services.users import get_profile_for_update, get_user_with_profile

from cards_app.utils.response_types import ResponseType

logger = logging.getLogger(__name__)


class ViewProfileUseCase:
    """
    Use case для просмотра профиля пользователя.
    Координирует получение данных профиля в зависимости от того, кто просматривает профиль.
    Возможны 3 случая: аноним, гость, хозяин
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            current_user: User | None,
            target_user_id: int
    ) -> ViewProfileUseCaseResponse:
        """
        Выполняет получение и подготовку данных профиля для отображения
        Args:
            current_user: User + Profile текущего пользователя
            target_user_id: ID Profile пользователя, чей профиль просматривается

        Returns:
            ViewProfileUseCaseResponse:
                - user_info (ProfileResponseDTO | None): DTO с полной информацией профиля
                - error_message (str | None): сообщение об ошибке
                - response_type (str): статус ответа.
        Note:
            - SUCCESS: успешное получение данных
            - NOT_FOUND: пользователь не найден
            - SERVER_ERROR: непредвиденная ошибка
        """

        try:
            # Для просмотра своей страницы все равно вызывается загрузка профиля, так как нужна еще и гильдия
            target_user = await get_base_info_profile(session_db=self.session_db, user_id=target_user_id)
        except UserNotFoundError as error:
            return ViewProfileUseCaseResponse(
                response_type=error.response_type,
                error_message=str(error),
                user_info=None
            )
        except Exception as error:
            logger.error(f'Непредвиденная ошибка в ViewProfileUseCase: {error}', exc_info=True)
            return ViewProfileUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                user_info=None
            )

        guild_dto = None
        if target_user.profile.guild:
            guild_dto = GuildBase(id=target_user.profile.guild.id, name=target_user.profile.guild.name)

        # 4. Избранная карта и амулет
        card_dto = None
        amulet_dto = None
        if target_user.profile.current_card_id:
            card = await get_card_with_details(
                session_db=self.session_db,
                card_id=target_user.profile.current_card_id
            )
            if card:
                card_dto = CardDTO(
                    id=card.id,
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
                    amulet_dto = AmuletBase(
                        id=card.amulet.id,
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
            fights = await get_user_fight_history(
                session_db=self.session_db,
                profile_id=target_user.profile.id,
                limit=50
            )
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

                battle_history.append(
                    FightHistoryRecordDTO(
                        date_and_time=fight.date_and_time,
                        result=result,
                        user_card=CardBase(
                            id=target_card.id,
                            class_card_name=target_card.class_card.name,
                            rarity_card_name=target_card.rarity_card.name,
                            type_card_name=target_card.type_card.name,
                            class_card_pic=target_card.class_card.image,
                            hp=target_card.hp,
                            damage=target_card.damage
                        ),
                        opponent_id=opponent_user.id,
                        opponent_username=opponent_user.username,
                        opponent_card=CardBase(
                            id=opponent_card.id,
                            class_card_name=opponent_card.class_card.name,
                            rarity_card_name=opponent_card.rarity_card.name,
                            type_card_name=opponent_card.type_card.name,
                            class_card_pic=opponent_card.class_card.image,
                            hp=opponent_card.hp,
                            damage=opponent_card.damage
                        )
                    )
                )

        elif current_user is not None:
            role = 'guest'
            if current_user.profile:
                stats = await get_battle_stats(
                    session_db=self.session_db,
                    profile1_id=current_user.profile.id,
                    profile2_id=target_user.profile.id
                )
                win_vs, lose_vs = stats
                is_fav = await is_favorite(
                    session_db=self.session_db,
                    current_profile_id=current_user.profile.id,
                    target_profile_id=target_user.profile.id
                )

        user_info = ProfileFullInfoDTO(
            id=target_user.id,
            username=target_user.username,
            about_user=target_user.profile.about_user,
            profile_pic=target_user.profile.profile_pic,
            win=target_user.profile.win,
            lose=target_user.profile.lose,
            rating=target_user.profile.rating,
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
        return ViewProfileUseCaseResponse(
            response_type=ResponseType.SUCCESS,
            error_message=None,
            user_info=user_info
        )


class AddFavoriteUserUseCase:
    """ Use case для добавления пользователя в список избранных """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            current_user_id: int | None,
            target_user_id: int
    ) -> ToggleFavoriteUserUseCaseResponse:
        """
        Добавляет целевого пользователя в избранное текущего.
        Args:
            current_user_id: ID User текущего пользователя
            target_user_id: ID Profile пользователя, которого нужно добавить в избранное.
        Returns:
            ToggleFavoriteUserUseCaseResponse:
                - error_message (str | None): сообщение об ошибке.
                - response_type (str): статус ответа.
                - success_message (str | None): сообщение об успехе.
        Note:
            - REDIRECT_WITH_INFO: успешное добавление.
            - REDIRECT_WITH_ERROR: Ошибка добавления.
            - UNAUTHORIZED: запрос неавторизованного пользователя.
            - NOT_FOUND: целевой пользователь не найден.
            - SERVER_ERROR: непредвиденная ошибка
        """

        if current_user_id is None:
            logger.warning(f'Попытка неавторизованного пользователя добавить пользователя в избранное')
            return ToggleFavoriteUserUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для добавления пользователя в список избранных вы должны быть авторизованы',
                success_message=None
            )

        await get_profile_for_update(session_db=self.session_db, user_id=current_user_id)
        current_user = await get_user_with_profile(session_db=self.session_db, user_id=current_user_id)

        if current_user is None:
            logger.warning(f'Попытка неавторизованного пользователя добавить пользователя в избранное')
            return ToggleFavoriteUserUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для добавления пользователя в список избранных вы должны быть авторизованы',
                success_message=None
            )

        try:

            await ensure_favorite_slot_available(self.session_db, current_user)
            await add_user_to_favorite(
                session_db=self.session_db,
                current_user_id=current_user.profile.id,
                target_user_id=target_user_id
            )

            await self.session_db.commit()
            return ToggleFavoriteUserUseCaseResponse(
                response_type=ResponseType.REDIRECT_WITH_INFO,
                error_message=None,
                success_message=f'Пользователь добавлен в избранное'
            )

        except (UserFavoriteException, NotEnoughSlotsError) as error:
            await self.session_db.rollback()
            return ToggleFavoriteUserUseCaseResponse(
                response_type=error.response_type,
                error_message=str(error),
                success_message=None
            )

        except Exception as error:
            await self.session_db.rollback()
            logger.error(f'Непредвиденная ошибка в AddFavoriteUserUseCase: {error}', exc_info=True)

            return ToggleFavoriteUserUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                success_message=None
            )


class RemoveFavoriteUserUseCase:
    """ Use case для удаления пользователя из списка избранных """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(
            self,
            current_user_id: int | None,
            target_user_id: int
    ) -> ToggleFavoriteUserUseCaseResponse:
        """
        Удаляет целевого пользователя из избранного текущего.
        Args:
            current_user_id: ID User текущего пользователя
            target_user_id: ID Profile пользователя, которого нужно удалить из избранного.
        Returns:
            ToggleFavoriteUserUseCaseResponse:
                - error_message (str | None): сообщение об ошибке.
                - response_type (str): статус ответа.
                - success_message (str | None): сообщение об успехе.
        Note:
            - REDIRECT_WITH_INFO: успешное добавление.
            - REDIRECT_WITH_ERROR: Ошибка добавления.
            - UNAUTHORIZED: запрос неавторизованного пользователя.
            - NOT_FOUND: целевой пользователь не найден.
            - SERVER_ERROR: непредвиденная ошибка
        """

        if current_user_id is None:
            logger.warning(f'Попытка неавторизованного пользователя удить пользователя из списка избранных')
            return ToggleFavoriteUserUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                success_message=None,
                error_message=f'Для удаления пользователя из списка избранных вы должны быть авторизованы'
            )

        await get_profile_for_update(session_db=self.session_db, user_id=current_user_id)
        current_user = await get_user_with_profile(session_db=self.session_db, user_id=current_user_id)

        if current_user is None:
            logger.warning(f'Попытка неавторизованного пользователя удить пользователя из списка избранных')
            return ToggleFavoriteUserUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                success_message=None,
                error_message=f'Для удаления пользователя из списка избранных вы должны быть авторизованы'
            )

        try:
            await remove_user_from_favorite(
                session_db=self.session_db,
                current_user_id=current_user.profile.id,
                target_user_id=target_user_id
            )

            await self.session_db.commit()
            return ToggleFavoriteUserUseCaseResponse(
                response_type=ResponseType.REDIRECT_WITH_INFO,
                success_message=f'Пользователь удален из избранного',
                error_message=None
            )

        except (UserNotFoundError, UserFavoriteException) as error:
            await self.session_db.rollback()
            return ToggleFavoriteUserUseCaseResponse(
                response_type=error.response_type,
                success_message=None,
                error_message=str(error)
            )

        except Exception as error:
            await self.session_db.rollback()
            logger.error(f'Непредвиденная ошибка в RemoveFavoriteUserUseCase: {error}', exc_info=True)
            return ToggleFavoriteUserUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                success_message=None,
                error_message=None
            )


class FavoriteUsersUseCase:
    """ Use case для просмотра списка избранных """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user: User | None) -> FavoriteUsersUseCaseResponse:
        """
        Формирует FavoriteUsersPageDTO для просмотра списка избранных пользователей
        Args:
            current_user: User + Profile текущего пользователя
        Returns:
            FavoriteUsersUseCaseResponse:
                - favorite_users (FavoriteUsersPageDTO | None): DTO избранных пользователей
                - error_message (str | None): сообщение об ошибке.
                - response_type (str): статус ответа.
        Note:
            - SUCCESS: успешное получение данных.
            - UNAUTHORIZED: неавторизованный пользователь.
            - SERVER_ERROR: любая ошибка.
        """

        if current_user is None:
            return FavoriteUsersUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                error_message=f'Для просмотра избранных вы должны быть авторизованы',
                favorite_users=None
            )

        try:
            all_favorite_users: list = await get_favorite_user(self.session_db, user_profile_id=current_user.profile.id)
            favorite_users = []
            for user in all_favorite_users:
                favorite_users.append(
                    FavoriteUserDTO(
                        id=user.favorite_user.id,
                        username=user.favorite_user.user.username
                    )
                )
            favorite_users_dto = FavoriteUsersPageDTO(
                amount_users=len(all_favorite_users),
                max_amount_users=current_user.profile.max_favorite,
                favorite_users=favorite_users
            )
            return FavoriteUsersUseCaseResponse(
                response_type=ResponseType.SUCCESS,
                error_message=None,
                favorite_users=favorite_users_dto
            )

        except Exception as error:
            await self.session_db.rollback()
            logger.error(f'Непредвиденная ошибка в FavoriteUsersUseCase: {error}', exc_info=True)
            return FavoriteUsersUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                error_message=None,
                favorite_users=None
            )


class UserTransactionsUseCase:
    """ Use case для просмотра транзакций """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self, current_user: User | None,
                      ) -> UserTransactionsUseCaseResponse:
        """
        Формирует TransactionsDTO пользователя
        Args:
            current_user: User + Profile текущего пользователя
        Returns:
            UserTransactionsUseCaseDict:
                - transactions (TransactionsDTO | None): DTO избранных пользователей
                - response_type (str): статус ответа.
                - error_message: текст ошибки.
        Note:
            - SUCCESS: успешное получение данных.
            - UNAUTHORIZED: если пользователь не авторизован.
            - SERVER_ERROR: любая другая ошибка.
        """

        if current_user is None:
            return UserTransactionsUseCaseResponse(
                response_type=ResponseType.UNAUTHORIZED,
                transactions=None
            )

        try:
            user_transactions: list = await get_user_transactions(session_db=self.session_db, user_id=current_user.id)
            user_transactions_dto = TransactionsDTO(
                transactions=[
                    RecordTransaction(
                        date_and_time=tx.date_and_time,
                        before=tx.before,
                        after=tx.after,
                        comment=tx.comment,
                        delta=tx.after - tx.before
                    )
                    for tx in user_transactions
                ],
            )

            return UserTransactionsUseCaseResponse(
                response_type=ResponseType.SUCCESS,
                transactions=user_transactions_dto
            )
        except Exception as error:
            logger.error(f'Непредвиденная ошибка в UserTransactionsUseCase: {error}', exc_info=True)
            return UserTransactionsUseCaseResponse(
                response_type=ResponseType.SERVER_ERROR,
                transactions=None
            )
