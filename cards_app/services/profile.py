import logging

from datetime import datetime
from math import ceil

from sqlalchemy import func, or_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cards_app.exeptions import (InsufficientFundsUserError, NotEnoughSlotsError, SelfFavoriteError,
                                 DuplicateFavoriteError, UserNotFoundError, SelfFavoriteRemoveError,
                                 FavoriteNotFoundError)
from cards_app.models import User, Profile, Card, FightHistory, Transactions, FavoriteUsers
from cards_app.services.cards import get_all_cards_user
from cards_app.types import AddGoldForFightDict

logger = logging.getLogger(__name__)


async def get_base_info_profile(session_db: AsyncSession, user_id: int
                                ) -> User:
    """ Возвращает базовую информацию профиля с подгруженной гильдией.
        Args:
            session_db: сессия базы данных
            user_id: ID User пользователя
        Returns:
            User: User + Profile + Guild
        Raises:
            UserNotFoundError: если пользователь с указанным ID не найден в БД.
    """

    stmt_user = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.profile)
            .selectinload(Profile.guild)
        )
    )
    result_user = await session_db.execute(stmt_user)
    user = result_user.scalar_one_or_none()
    if user is None:
        logger.warning(f'Пользователь ID {user_id} не найден')
        raise UserNotFoundError(user_id)
    return user


async def get_battle_stats(session_db: AsyncSession, profile1_id: int, profile2_id: int
                           ) -> tuple[int, int]:
    """ Возвращает статистику побед / поражений пользователя против другого.
        Args:
            session_db: сессия базы данных
            profile1_id: ID профиля текущего пользователя
            profile2_id: ID профиля соперника
        Returns:
            tuple[int, int]: кортеж побед и поражений текущего пользователя против соперника, либо 0, 0
    """

    wins = await session_db.scalar(
        select(func.count())
        .where(
            FightHistory.winner_id == profile1_id,
            or_(
                FightHistory.participant1_id == profile2_id,
                FightHistory.participant2_id == profile2_id
            )
        )
    )
    loses = await session_db.scalar(
        select(func.count())
        .where(
            FightHistory.winner_id == profile2_id,
            or_(
                FightHistory.participant1_id == profile1_id,
                FightHistory.participant2_id == profile1_id
            )
        )
    )

    return wins or 0, loses or 0


async def get_user_fight_history(session_db: AsyncSession, profile_id: int, limit: int = 50
                                 ) -> list[FightHistory]:
    """ Возвращает список боёв, где профиль был участником, с подгрузкой соперника и карт.
         Args:
            session_db: сессия базы данных
            profile_id: ID профиля, историю боёв которого нужно получить
            limit: максимальное количество возвращаемых записей. По умолчанию 50

        Returns:
            list[FightHistory]: список объектов FightHistory, отсортированных по дате
            от новых к старым. Каждый объект содержит подгруженные связи
    """

    stmt_battle_history = (
        select(FightHistory)
        .where(
            or_(
                FightHistory.participant1_id == profile_id,
                FightHistory.participant2_id == profile_id
            )
        )
        .order_by(desc(FightHistory.date_and_time))
        .limit(limit)
        .options(
            selectinload(FightHistory.participant1).selectinload(Profile.user),
            selectinload(FightHistory.participant2).selectinload(Profile.user),
            selectinload(FightHistory.winner),
            selectinload(FightHistory.card1).selectinload(Card.class_card),
            selectinload(FightHistory.card1).selectinload(Card.type_card),
            selectinload(FightHistory.card2).selectinload(Card.class_card),
            selectinload(FightHistory.card2).selectinload(Card.type_card),
        )
    )
    result = await session_db.execute(stmt_battle_history)
    battle_history = list(result.scalars().all())
    return battle_history


async def is_favorite(session_db: AsyncSession, current_profile_id: int, target_profile_id: int
                      ) -> bool:
    """ Возвращает флаг о том, находится ли выбранный пользователь в списке избранных у текущего.
        Args:
            session_db: сессия базы данных
            current_profile_id: ID профиля текущего пользователя
            target_profile_id: ID профиля целевого пользователя

        Returns:
            bool: True, если target_profile_id есть в избранном у current_profile_id, иначе False.
    """

    stmt_user = (
        select(FavoriteUsers)
        .where(FavoriteUsers.user_id == current_profile_id,
               FavoriteUsers.favorite_user_id == target_profile_id
               )
    )
    result = await session_db.execute(stmt_user)
    return result.scalar_one_or_none() is not None


async def update_user_receiving_timer(session_db: AsyncSession, current_user: User) -> None:
    """ Обновление таймера при получении бесплатной карты.
        Args:
            session_db: сессия базы данных
            current_user: объект User текущего пользователя
    """

    current_user.profile.receiving_timer = datetime.now()
    session_db.add(current_user.profile)
    logger.info(f'Пользователь ID {current_user.profile.id} обновил таймер получения')


async def check_can_user_receive_card(session_db: AsyncSession, current_user: User, need_slots: int
                                      ) -> None:
    """ Проверяет, хватит ли у пользователя места в инвентаре для новых карт.
        Args:
            session_db: сессия базы данных
            current_user: объект User + Profile текущего пользователя
            need_slots: количество слотов, необходимых для новых карт
        Raises:
            NotEnoughSlotsError: если свободных слотов меньше, чем необходимо
    """

    all_cards = await get_all_cards_user(session_db, current_user.profile.id)
    if need_slots > current_user.profile.card_slots - len(all_cards):
        logger.warning(f'Пользователь ID {current_user.profile.id} пытается получить карту, но не хватает слотов '
                       f'(нужно {need_slots}, свободно {current_user.profile.card_slots - len(all_cards)})')
        raise NotEnoughSlotsError('У вас недостаточно места для новых карт')


async def charge_user_gold(session_db: AsyncSession,
                           current_user: User,
                           need_gold: int
                           ) -> dict[str, int]:
    """ Списывает золото у пользователя.
        Args:
            session_db: сессия базы данных
            current_user: объект текущего пользователя (User) с подгруженным профилем
            need_gold: количество золота для списания.
        Returns:
            dict:
                - gold_before (int): количество золота до списания
                - gold_after (int): количество золота после списания
        Raises:
            InsufficientFundsUserError: если у пользователя недостаточно золота.
    """

    answer_data = {'gold_before': None,
                   'gold_after': None}

    if current_user.profile.gold < need_gold:
        logger.warning(f'Попытка пользователя ID {current_user.profile.id} списать {need_gold} золота, '
                       f'но у него только {current_user.profile.gold}')
        raise InsufficientFundsUserError(need_gold - current_user.profile.gold)

    gold_after_buy = current_user.profile.gold - need_gold
    answer_data['gold_before'] = current_user.profile.gold
    answer_data['gold_after'] = gold_after_buy
    current_user.profile.gold = gold_after_buy

    session_db.add(current_user)
    logger.info(f'Списано {need_gold} золота у пользователя ID {current_user.profile.id}: '
                f'{answer_data["gold_before"]} → {gold_after_buy}')

    return answer_data


async def add_user_gold(session_db: AsyncSession,
                        current_user: User,
                        add_gold: int
                        ) -> dict[str, int]:
    """ Добавляет пользователю золото.
        Args:
            session_db: сессия базы данных
            current_user: User + Profile текущего пользователя
            add_gold: количество полученного золота
        Returns:
            dict:
                - gold_before (int): количество золота до списания.
                - gold_after (int): количество золота после списания.
        Raises:
            InsufficientFundsUserError: если у пользователя недостаточно золота.
    """

    answer_data = {'gold_before': None,
                   'gold_after': None}

    answer_data['gold_before'] = current_user.profile.gold
    gold_after = current_user.profile.gold + add_gold
    answer_data['gold_after'] = gold_after
    current_user.profile.gold = gold_after

    session_db.add(current_user)
    logger.info(f'Пользователь ID {current_user.id} получил {add_gold} золота')

    return answer_data


async def create_transaction(session_db: AsyncSession,
                             user_profile_id: int,
                             gold_before: int,
                             gold_after: int,
                             comment: str
                             ) -> None:
    """ Создает транзакцию пользователя.
        Args:
            session_db: сессия базы данных
            user_profile_id: ID профиля текущего пользователя
            gold_before: количество золота до списания
            gold_after: количество золота после списания
            comment: цель траты
    """

    new_transaction = Transactions(date_and_time=datetime.now(),
                                   user_id=user_profile_id,
                                   before=gold_before,
                                   after=gold_after,
                                   comment=comment)
    session_db.add(new_transaction)
    logger.debug(f'Создана транзакция для пользователя ID {user_profile_id}: '
                 f'{comment} (было {gold_before} → стало {gold_after})')


async def add_user_to_favorite(session_db: AsyncSession,
                               current_user_id: int,
                               target_user_id: int
                               ) -> None:
    """ Добавляет выбранного пользователя в список избранных текущего пользователя.
        Args:
            session_db: сессия базы данных.
            current_user_id: ID профиля текущего пользователя.
            target_user_id: ID профиля пользователя, которого добавляют в избранное.

        Raises:
            SelfFavoriteError: попытка добавить самого себя
            UserNotFoundError: профиль target_user_id не найден.
            DuplicateFavoriteError: пользователь уже есть в избранном.
    """

    if current_user_id == target_user_id:
        logger.warning(f'Пользователь ID {current_user_id} попытался добавить самого себя в избранное')
        raise SelfFavoriteError()

    target_user = await session_db.get(Profile, target_user_id)
    if target_user is None:
        logger.warning(f'Не найден профиль ID {target_user_id} при добавлении в избранное')
        raise UserNotFoundError()

    stmt_check = (
        select(FavoriteUsers)
        .where(FavoriteUsers.user_id == current_user_id,
               FavoriteUsers.favorite_user_id == target_user_id
               )
    )
    result = await session_db.execute(stmt_check)
    existing = result.scalar_one_or_none()
    if existing:
        logger.warning(f'Пользователь ID {current_user_id} уже имеет в избранном профиль {target_user_id}')
        raise DuplicateFavoriteError()
    new_favorite = FavoriteUsers(user_id=current_user_id, favorite_user_id=target_user_id)

    session_db.add(new_favorite)
    logger.info(f'Пользователь ID {current_user_id} добавил профиль {target_user_id} в избранное')


async def remove_user_from_favorite(session_db: AsyncSession,
                                    current_user_id: int,
                                    target_user_id: int
                                    ) -> None:
    """ Удаляет выбранного пользователя из списка избранных текущего пользователя.
        Args:
            session_db: сессия базы данных.
            current_user_id: ID профиля текущего пользователя
            target_user_id: ID профиля пользователя, которого пытаются удалить из избранного

        Raises:
            SelfFavoriteError: попытка удалить самого себя.
            UserNotFoundError: профиль target_user_id не найден.
            FavoriteNotFoundError: пользователь не найден в списке избранных
    """

    if current_user_id == target_user_id:
        logger.warning(f'Пользователь ID {current_user_id} попытался удалить самого себя из избранного')
        raise SelfFavoriteRemoveError()

    target_user = await session_db.get(Profile, target_user_id)
    if target_user is None:
        logger.warning(f'Не найден профиль ID {target_user_id} при удалении из избранного')
        raise UserNotFoundError()

    stmt_check = (
        select(FavoriteUsers)
        .where(FavoriteUsers.user_id == current_user_id,
               FavoriteUsers.favorite_user_id == target_user_id
               )
    )
    result = await session_db.execute(stmt_check)
    favorite = result.scalar_one_or_none()
    if not favorite:
        logger.warning(f'Запись об избранном не найдена: пользователь ID {current_user_id}, профиль {target_user_id}')
        raise FavoriteNotFoundError()
    await session_db.delete(favorite)
    logger.info(f'Пользователь ID {current_user_id} удалил профиль {target_user_id} из избранного')


async def ensure_favorite_slot_available(session_db: AsyncSession, current_user: User
                                         ) -> None:
    """ Проверяет, что у пользователя есть место для добавления нового пользователя в избранное.
        Args:
            session_db: сессия базы данных
            current_user: объект пользователя
        Raises:
            NotEnoughSlotsError: недостаточно места для добавления в избранное нового пользователя
    """

    stmt_count_fav_users = (
        select(func.count())
        .select_from(FavoriteUsers)
        .where(FavoriteUsers.user_id == current_user.profile.id
               )
    )
    result = await session_db.execute(stmt_count_fav_users)
    favorites_count = result.scalar_one()

    if favorites_count >= current_user.profile.max_favorite:
        logger.warning(f'Пользователь ID {current_user.profile.id} достиг лимита количества избранных')
        raise NotEnoughSlotsError('У вас недостаточно места в списке избранных для добавления нового пользователя')


async def get_favorite_user(session_db: AsyncSession, user_profile_id: int
                            ) -> list[FavoriteUsers]:
    """ Возвращает список избранных пользователей.
        Args:
            session_db: сессия базы данных
            user_profile_id: ID профиля пользователя
        Returns:
            list [FavoriteUsers]: список избранных пользователей
    """

    stmt_fav_users = (
        select(FavoriteUsers)
        .where(FavoriteUsers.user_id == user_profile_id)
        .options(
            selectinload(FavoriteUsers.favorite_user).selectinload(Profile.user)
        )
    )
    result = await session_db.execute(stmt_fav_users)
    favorite_users = list(result.scalars().all())

    return favorite_users


async def update_win_lose(session_db: AsyncSession,
                          winner=User,
                          loser=User
                          ) -> None:
    """ Обновляет статистику побед/поражений у пользователей после битвы.
        Вызывается только если у битвы был победитель.
        Args:
            session_db: сессия базы данных
            winner: User + Profile победителя
            loser: User + Profile проигравшего
    """

    winner.profile.win += 1
    loser.profile.lose += 1
    session_db.add(winner)
    session_db.add(loser)


async def add_gold_for_fight(session_db: AsyncSession,
                             user: User,
                             result_battle: str
                             ) -> AddGoldForFightDict:
    """ Вычисляет количество золота, которое должен получить пользователь за участие в битве,
        затем вызывает функцию начисления золота.
        Количество золота зависит от итога боя и наличия усиления гильдии.
        Args:
            session_db: сессия базы данных
            user: User + Profile участника боя
            result_battle: итог боя
        Returns:
            AddGoldForFightDict:
                - gold_before (int): золото до получения награды
                - gold_after (int): золото после получения награды
                - comment (str): строка пояснение для создания транзакции
        Raises:
            ValueError: если итог боя был
    """

    gold_for_win = 100
    gold_for_draw = 75
    gold_for_lose = 50

    if result_battle == 'win':
        comment = 'Награда за победу в битве'
        if user.profile.guild and user.profile.guild.buff.name == 'Бандитский улов':
            reward_gold = ceil(gold_for_win * user.profile.guild.buff.numeric_value / 100)
        else:
            reward_gold = gold_for_win
    elif result_battle == 'lose':
        comment = 'Награда за поражение в битве'
        reward_gold = gold_for_lose
    elif result_battle == 'draw':
        comment = 'Награда за ничью в битве'
        reward_gold = gold_for_draw
    else:
        raise ValueError(f'Принят неверный результат битвы result_battle: {result_battle}')

    answer_data: dict = await add_user_gold(session_db=session_db,
                                            current_user=user,
                                            add_gold=reward_gold)
    answer_data['comment'] = comment
    return answer_data


async def update_rating_user(session_db: AsyncSession, user: User, user_fight_result: str
                             ) -> None:
    """ Обновляет рейтинг участника битвы. При победе/поражении начисляет/отнимает 25 рейтинга пользователя.
        При ничьей начисляет 5 очков.
        Args:
            session_db: сессия базы данных
            user: User + Profile участника битвы
            user_fight_result: итог битвы для пользователя win/lose/draw
    """

    win_delta = 25
    draw_delta = 5

    if user_fight_result == 'draw':
        user.profile.rating += draw_delta
    elif user_fight_result == 'win':
        user.profile.rating += win_delta
    else:
        user.profile.rating = max(0, user.profile.rating - win_delta)

    session_db.add(user)


async def get_rating_users(session_db: AsyncSession, limit: int, offset: int
                           ) -> list[User]:
    """ Возвращает таблицу рейтинга с пагинацией, отсортированный по уменьшению рейтинга.
        Args:
            session_db: сессия базы данных
            limit: максимальное количество пользователей в одной странице
            offset: сдвиг для пагинации
        Returns:
            list[User]: список пользователей с профилем
    """

    stmt_users = (
        select(User)
        .join(Profile, User.id == Profile.user_id)
        .where(Profile.current_card_id.is_not(None))
        .order_by(Profile.rating.desc())
        .options(selectinload(User.profile))
        .limit(limit)
        .offset(offset)
    )
    result = await session_db.execute(stmt_users)
    users = list(result.scalars().all())
    return users


async def get_total_users_count(session_db: AsyncSession) -> int:
    """ Возвращает общее количество пользователей рейтинга для пагинации
        Args:
            session_db: сессия базы данных

        Returns:
            int: общее число записей в таблице Users.
    """

    stmt_count = (
        select(func.count())
        .select_from(User)
        .join(Profile, User.id == Profile.user_id)
        .where(Profile.current_card_id.is_not(None))
    )
    result = await session_db.execute(stmt_count)
    count = result.scalar_one()
    return count
