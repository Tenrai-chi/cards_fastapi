from random import randint

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, or_, desc

from cards_app.exeptions import SelfFightError, UserNotFoundError, CooldownNotElapsedError, NoCurrentCardError
from cards_app.models import User, FightHistory, Card, AmuletItem, Profile
from cards_app.types import FightNowDataDict
from cards_app.utils.common import time_difference_check


async def validate_battle_preconditions(session_db: AsyncSession,
                                        user_id: int,
                                        enemy_id: int,
                                        ) -> dict[str, User]:
    """ Проверка на возможность проведения рейтингового боя между 2 участниками.
        Args:
            session_db: сессия базы данных
            user_id: ID User нападающего (текущего) пользователя
            enemy_id: ID User противника
        Returns:
            dict:
                - user (User+Profile): текущий пользователь
                - enemy (User+Profile): противник
        Raises:
            SelfFightError: если пользователь нападает сам на себя
            UserNotFoundError: если противник не найден
            NoCurrentCardError: если у участника/ов не выбраны карты для боя
            CooldownNotElapsedError: из check_last_fight, если после последней битвы прошло недостаточно времени
    """

    answer_data = {'user': None,
                   'enemy': None}
    if user_id == enemy_id:
        raise SelfFightError()

    # Получение user+profile участников битвы
    stmt_user = (
        select(User).where(User.id == user_id)
        .options(
            selectinload(User.profile).selectinload(Profile.guild)
        )
    )
    user_result = await session_db.execute(stmt_user)
    user = user_result.scalar_one_or_none()

    stmt_enemy = (
        select(User)
        .where(User.id == enemy_id)
        .options(
            selectinload(User.profile).selectinload(Profile.guild)
        )
    )
    enemy_result = await session_db.execute(stmt_enemy)
    enemy = enemy_result.scalar_one_or_none()

    if enemy is None:
        raise UserNotFoundError()
    if not user.profile.current_card_id:
        raise NoCurrentCardError(user.username)
    if not enemy.profile.current_card_id:
        raise NoCurrentCardError(enemy.username)

    await check_last_fight(session_db=session_db,
                           user_profile_id=user_id,
                           enemy_profile_id=enemy_id)

    answer_data['user'] = user
    answer_data['enemy'] = enemy
    return answer_data


async def check_last_fight(session_db: AsyncSession,
                           user_profile_id: int,
                           enemy_profile_id: int
                           ) -> None:
    """ Получает последний бой между пользователями и проверяет, что прошло достаточно времени
        Если не прошло достаточно времени, то поднимает ошибку CooldownNotElapsedError
        Args:
            session_db: сессия базы данных
            user_profile_id: ID профиля текущего пользователя
            enemy_profile_id: ID профиля противника
        Raises:
            CooldownNotElapsedError: если не прошло достаточно времени после предыдущей битвы
    """

    stmt_last_fight = (
        select(FightHistory).where(
            or_(
                (FightHistory.winner_id == enemy_profile_id) & (FightHistory.loser_id == user_profile_id),
                (FightHistory.winner_id == user_profile_id) & (FightHistory.loser_id == enemy_profile_id)
            )
        ).order_by(desc(FightHistory.id)).limit(1)
    )

    result = await session_db.execute(stmt_last_fight)
    last_fight = result.scalar_one_or_none()

    if last_fight is not None:
        can_fight, hours = time_difference_check(last_fight.date_and_time, 6)
        if not can_fight:
            base_message = f'Вы не можете бросить вызов этому пользователю'
            raise CooldownNotElapsedError(base_message=base_message, hours=hours)


async def get_cards_participants(session_db: AsyncSession,
                                 user_card_id: int,
                                 enemy_card_id: int
                                 ) -> dict[str, Card]:
    """ Возвращает карты участников с подгруженными амулетами.
        Args:
            session_db: сессия базы данных
            user_card_id: ID карты текущего пользователя
            enemy_card_id: ID карты противника
        Returns:
            dict:
                - user_card: карта текущего пользователя
                - enemy_card: карта противника
    """

    stmt_cards = (
        select(Card).where(
            Card.id.in_([user_card_id, enemy_card_id])
        ).options(
            selectinload(Card.amulet).selectinload(AmuletItem.amulet_type),
            selectinload(Card.class_card),
            selectinload(Card.type_card),
            selectinload(Card.rarity_card)
        )
    )

    result = await session_db.execute(stmt_cards)
    cards = {card.id: card for card in result.scalars()}

    user_card = cards.get(user_card_id)
    enemy_card = cards.get(enemy_card_id)

    return {'user_card': user_card,
            'enemy_card': enemy_card}


def stats_calculation(user_card: Card,
                      enemy_card: Card
                      ) -> tuple[float, float, float, float]:
    """ Вычисляет конечные характеристики карт с учетом амулета и типов.
        Args:
            user_card: Card текущего пользователя
            enemy_card: Card противника
        Returns:
            tuple:
                - Здоровье карты текущего пользователя
                - Урон карты текущего пользователя
                - Здоровье карты противника
                - Урон карты противника
    """

    user_card_hp = round(user_card.hp, 2)
    user_card_damage = round(user_card.damage, 2)
    enemy_card_hp = round(enemy_card.hp, 2)
    enemy_card_damage = round(enemy_card.damage, 2)

    if user_card.type_card.better.id == enemy_card.type_card.id:
        user_card_damage = round(user_card_damage * 1.2, 2)
        enemy_card_damage = round(enemy_card_damage * 0.8, 2)
    # Если карта противника лучше карты пользователя
    elif enemy_card.type_card.better.id == user_card.type_card.id:
        enemy_card_damage = round(enemy_card_damage * 1.2, 2)
        user_card_damage = round(user_card_damage * 0.8, 2)

    user_amulet_type = user_card.amulet.amulet_type if user_card.amulet else None
    enemy_amulet_type = enemy_card.amulet.amulet_type if enemy_card.amulet else None

    if user_amulet_type:
        user_card_hp += user_amulet_type.bonus_hp or 0.0
        user_card_damage += user_amulet_type.bonus_damage or 0.0

    if enemy_amulet_type:
        enemy_card_hp += enemy_amulet_type.bonus_hp or 0.0
        enemy_card_damage += enemy_amulet_type.bonus_damage or 0.0

    return user_card_hp, user_card_damage, enemy_card_hp, enemy_card_damage


def fight_now(user: User,
              enemy: User,
              user_card: Card,
              enemy_card: Card
              ) -> FightNowDataDict:
    """ Принимает пользователей и их карты с подгруженными данными и проводит бой.
        Если в битве есть победитель, то возвращает winner и loser,
        иначе оба None
        Args:
            user: User + Profile текущего пользователя
            enemy: User + Profile противника
            user_card: Card текущего пользователя с амулетом, типом, классом и редкостью
            enemy_card: Card противника с амулетом, типом, классом и редкостью
        Returns:
            dict FightNowDataDict:
                - is_victory (bool): True, если есть победитель
                - winner (User | None): User, если есть победитель
                - loser (User | None): User, если есть победитель
                - history_fight (list[str]): история боя
    """

    answer_data: FightNowDataDict = {'is_victory': None,
                                     'winner': None,
                                     'loser': None,
                                     'history_fight': None}
    user_hp, user_damage, enemy_hp, enemy_damage = stats_calculation(user_card, enemy_card)

    history_fight = []
    turn = 0

    while True:
        # Ход пользователя
        user_hp, user_damage, enemy_hp, enemy_damage, history = process_turn(attacker_card=user_card,
                                                                             attacker_hp=user_hp,
                                                                             attacker_damage=user_damage,
                                                                             defender_card=enemy_card,
                                                                             defender_hp=enemy_hp,
                                                                             defender_damage=enemy_damage,
                                                                             turn_number=turn + 1
                                                                             )
        history_fight.append(history)
        if enemy_hp <= 0 or user_hp <= 0:
            break

        # Ход противника
        enemy_hp, enemy_damage, user_hp, user_damage, history = process_turn(attacker_card=enemy_card,
                                                                             attacker_hp=enemy_hp,
                                                                             attacker_damage=enemy_damage,
                                                                             defender_card=user_card,
                                                                             defender_hp=user_hp,
                                                                             defender_damage=user_damage,
                                                                             turn_number=turn + 2
                                                                             )
        history_fight.append(history)
        if user_hp <= 0 or enemy_hp <= 0:
            break

        turn += 2  # увеличиваем номер хода

    # Определение победителя
    if user_hp <= 0 and enemy_hp <= 0:
        winner = None
        loser = None
        is_victory = False
    elif user_hp <= 0:
        winner = enemy
        loser = user
        is_victory = True
    else:  # enemy_hp <= 0
        winner = user
        loser = enemy
        is_victory = True

    answer_data['is_victory'] = is_victory
    answer_data['winner'] = winner
    answer_data['loser'] = loser
    answer_data['history_fight'] = history_fight
    return answer_data


def process_turn(attacker_card: Card,
                 attacker_hp: float,
                 attacker_damage: float,
                 defender_card: Card,
                 defender_hp: float,
                 defender_damage: float,
                 turn_number: int
                 ) -> tuple[float, float, float, float, list[str]]:
    """ Обрабатывает один ход. Возвращает обновленные характеристики здоровья и урона,
        а также историю хода.
        Args:
            attacker_card: объект атакующей карты
            attacker_hp: здоровье атакующей карты
            attacker_damage: урон атакующей карты
            defender_card: объект обороняющейся карты
            defender_hp: здоровье обороняющейся карты
            defender_damage: урон обороняющейся карты
            turn_number: номер хода
        Returns:
            tuple:
                - float: здоровье атакующей карты
                - float: урон атакующей карты
                - float: здоровье обороняющейся карты
                - float: урон обороняющейся карты
                - list[str]: запись истории хода
    """
    
    history = [f'Ход {turn_number} {attacker_card.owner.user.username}']
    # Способности защитника, срабатывающие до получения урона
    # Дриада (лечение защитника)
    if defender_card.class_card.name == 'Дриада':
        defender_hp, heal = use_spell_dryad(defender_card, defender_hp)
        history.append(formation_of_history(defender_card, heal))

    # Жнец (изменение урона атакующего и защитника)
    if attacker_card.class_card.name == 'Жнец':
        result = use_spell_reaper(attacker_card, attacker_damage, defender_damage)
        if result:
            attacker_damage, defender_damage, change = result
            history.append(formation_of_history(attacker_card, change))

    # Атака
    defender_hp = round(defender_hp - attacker_damage, 2)
    history.append(f'{attacker_card.owner.user.username} наносит {attacker_damage} урона')

    # Способности атакующего, срабатывающие после атаки
    if attacker_card.class_card.name == 'Берсерк':
        attacker_damage, change = use_spell_berserk(attacker_card, attacker_damage)
        history.append(formation_of_history(attacker_card, change))

    if attacker_card.class_card.name == 'Демон':
        result = use_spell_demon(attacker_card, attacker_damage, defender_hp)
        if result:
            defender_hp, add_damage = result
            history.append(formation_of_history(attacker_card, add_damage))

    if attacker_card.class_card.name == 'Оборотень':
        result = use_spell_werewolf(attacker_card, attacker_hp, attacker_damage)
        if result:
            attacker_hp, regen_hp = result
            history.append(formation_of_history(attacker_card, regen_hp))

    if defender_card.class_card.name == 'Призрак':  # Защитник уклоняется
        result = use_spell_ghost(defender_card, defender_hp, attacker_damage)
        if result:
            defender_hp, evade_damage = result
            history.append(formation_of_history(defender_card, evade_damage))

    if defender_card.class_card.name == 'Бог Император':  # Защитник отражает урон
        attacker_hp, return_damage = use_spell_emperor_mankind(defender_card, attacker_damage, attacker_hp)
        history.append(formation_of_history(defender_card, return_damage))

    history.append(f'Здоровье {attacker_card.owner.user.username} {attacker_hp}')
    history.append(f'Здоровье {defender_card.owner.user.username} {defender_hp}')

    return attacker_hp, attacker_damage, defender_hp, defender_damage, history


def use_spell_dryad(card: Card, card_hp: float) -> tuple[float, float]:
    """ Использование способности дриады.
        Восстанавливает свое здоровье в зависимости от уровня слияния.
        Возвращает итоговое количество своего здоровья и полученное лечение.
        Args:
            card: карта класса дриада
            card_hp: текущее здоровье карты
        Returns:
            tuple:
                - float: итоговое здоровье карты
                - float: количество восстановленного здоровья

    """

    heal_hp = card.class_card.numeric_value + 5 * card.merger
    card_hp += heal_hp

    return card_hp, heal_hp


def use_spell_demon(card: Card, card_damage: float, enemy_card_hp: float
                    ) -> tuple[float, float] | None:
    """ Использование способности демона.
        Если сработал шанс, то наносит дополнительный урон, зависящий от атаки и уровня слияния.
        Возвращает итоговое количество вражеского здоровья и дополнительный урон или None при неудаче.
        Args:
            card: карта класса демон
            card_damage: урон карты
            enemy_card_hp: текущее здоровье карты противника
        Returns:
            tuple:
                - float: итоговое здоровье карты противника
                - float: нанесенный способностью дополнительный урон
            None:
                - Если способность не была использована
    """

    chance = randint(1, 100)
    if chance <= card.class_card.chance_use:
        additional_damage = round(card_damage * (card.class_card.numeric_value + 5 * card.merger) / 100, 2)
        enemy_card_hp = round(enemy_card_hp - additional_damage, 2)

        return enemy_card_hp, additional_damage


def use_spell_werewolf(card: Card, card_hp: float, card_damage: float
                       ) -> tuple[float, float] | None:
    """ Использование способности оборотня.
        Если сработал шанс, то восстанавливает свое здоровье, зависящее от его урона и уровня слияния.
        Возвращает итоговое количество своего здоровья и количество восполненного здоровья или None при неудаче.
        Args:
            card: карта класса оборотень
            card_hp: здоровье карты
            card_damage: урон карты
        Returns:
            tuple:
                - float: итоговое здоровье карты
                - float: количество восстановленного здоровья
            None:
                - Если способность не была использована
    """

    chance = randint(1, 100)
    if chance <= card.class_card.chance_use:
        regen_hp = round(card_damage * (card.class_card.numeric_value + 2 * card.merger) / 100, 2)
        card_hp = round(card_hp + regen_hp, 2)

        return card_hp, regen_hp


def use_spell_ghost(card: Card, card_hp: float, enemy_damage: float) -> tuple[float, float] | None:
    """ Использование способности призрака.
        Если сработал шанс, призрак избегает урон от атаки противника (восполнятся здоровье)
        Возвращает итоговое количество своего здоровья или None при неудаче.
        Args:
            card: карта класса призрак
            card_hp: текущее здоровье карты
            enemy_damage: урон карты противника
        Returns:
            tuple:
                - float: итоговое здоровье карты
                - float: количество восстановленного здоровья
            None:
                - Если способность не была использована
    """

    chance = randint(1, 100)
    if chance <= card.class_card.chance_use + 2.5 * card.merger:
        card_hp = round(card_hp + enemy_damage, 2)

        return card_hp, enemy_damage


def use_spell_emperor_mankind(card: Card, enemy_damage: float, enemy_hp: float) -> tuple[float, float]:
    """ Использование способности императора человечества.
        Наносит часть полученного урона атаковавшему.
        Возвращает итоговое количество здоровья нападающего, и количество возвращенного урона.
        Args:
            card: карта класса бог император
            enemy_damage: урон карты противника
            enemy_hp: здоровье карты противника
        Returns:
            tuple:
                - float: итоговое здоровье карты противника
                - float: количество возвращенного урона
    """

    return_damage = round((card.class_card.numeric_value + 3 * card.merger) * enemy_damage / 100, 2)
    enemy_hp = round(enemy_hp - return_damage, 2)

    return enemy_hp, return_damage


def use_spell_berserk(card: Card, card_damage: float) -> tuple[float, float]:
    """ Использование способности берсерка.
        Увеличивает свой урон после атаки.
        Возвращает итоговое значение своего урона.
        Args:
            card: карта класса берсерк
            card_damage: текущий урон карты
        Returns:
            tuple:
                - float: итоговый урон карты
                - float: количество увеличенного урона
    """

    change = round(1 + 0.5 * card.merger, 2)
    up_damage = round(card_damage + change, 2)

    return up_damage, change


def use_spell_reaper(card: Card, card_damage: float, enemy_card_damage: float
                     ) -> tuple[float, float, float] | None:
    """ Использование способности жнеца.
        Если сработал шанс, понижает урон противника и повышает свой.
        Возвращает итоговые значения урона карты пользователя и карты противника или None при неудаче.
        Args:
            card: карта класса жнец
            card_damage: текущий урон карты
            enemy_card_damage: текущий урон карты противника
        Returns:
            tuple:
                - float: итоговый урон карты
                - float: итоговый урон карты противника
                - float: количество повышенного и пониженного урона (одинаковое для всех)
            None:
                - Если способность не была использована
    """

    chance = randint(1, 100)
    if chance <= card.class_card.chance_use + 0.8 * card.merger:
        change = round(enemy_card_damage * (card.class_card.numeric_value + 2 * card.merger) / 100, 2)
        card_damage = round(card_damage + change, 2)
        enemy_card_damage = round(enemy_card_damage - change, 2)

        return card_damage, enemy_card_damage, change


def formation_of_history(card: Card, value: float) -> str:
    """ Формирование текста для записи в историю ходов
        при использовании способности карты
        Args:
            card: карта использующая способность
            value: значение способности (уронЮ обновление характеристик и тд)
        Returns:
            str: Строка с описанием использования способности
    """

    description_move = (f'Используется способность {card.owner.user.username}-' +
                        f'{card.class_card.name} ' +
                        f'"{card.class_card.skill}" и ' +
                        f'{card.class_card.description_for_history_fight} ' +
                        f'{value}')

    return description_move
