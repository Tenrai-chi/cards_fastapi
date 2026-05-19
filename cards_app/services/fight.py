from random import randint
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, or_, desc

from cards_app.exeptions import SelfFightError, UserNotFoundError, CooldownNotElapsedError, NoCurrentCardError
from cards_app.models import User, FightHistory, Card, AmuletItem, Profile
from cards_app.utils.common import time_difference_check


async def validate_battle_preconditions(session_db: AsyncSession,
                                        attacker_id: int,
                                        protector_id: int,
                                        ) -> dict[str, User]:
    """ Проверка на возможность проведения рейтингового боя между 2 участниками.
        Args:
            session_db: сессия базы данных
            attacker_id: ID нападающего (текущего) пользователя
            protector_id: ID противника
        Returns:
            dict:
                - attacker (User+Profile): текущий пользователь
                - protector (User+Profile): противник
        Raises:
            SelfFightError: если пользователь нападает сам на себя
    """

    answer_data = {'attacker': None,
                   'protector': None}
    if attacker_id == protector_id:
        raise SelfFightError()

    # Получение профиля + user для нападения и защиты
    attacker_result = await session_db.execute(
        select(User)
        .where(User.id == attacker_id)
        .options(
            selectinload(User.profile).selectinload(Profile.guild)
        )
    )
    attacker = attacker_result.scalar_one_or_none()

    protector_result = await session_db.execute(
        select(User)
        .where(User.id == protector_id)
        .options(
            selectinload(User.profile).selectinload(Profile.guild)
        )
    )
    protector = protector_result.scalar_one_or_none()

    if protector is None:
        raise UserNotFoundError()
    if not attacker.profile.current_card_id:
        raise NoCurrentCardError(attacker.username)
    if not protector.profile.current_card_id:
        raise NoCurrentCardError(protector.username)

    await check_last_fight(session_db=session_db,
                           attacker_id=attacker_id,
                           protector_id=protector_id)

    answer_data['attacker'] = attacker
    answer_data['protector'] = protector
    return answer_data


async def check_last_fight(session_db: AsyncSession,
                           attacker_id: int,
                           protector_id: int
                           ) -> None:
    """ Получает последний бой между пользователями.
        Если не прошло достаточно времени, то поднимает ошибку CooldownNotElapsedError
        Args:
            session_db: сессия базы данных
            attacker_id: ID текущего пользователя
            protector_id: ID противника
        Raises:
            CooldownNotElapsedError: если не прошло достаточно времени после предыдущей битвы
    """

    stmt = select(FightHistory).where(
        or_(
            (FightHistory.winner_id == protector_id) & (FightHistory.loser_id == attacker_id),
            (FightHistory.winner_id == attacker_id) & (FightHistory.loser_id == protector_id)
        )
    ).order_by(desc(FightHistory.id)).limit(1)

    result = await session_db.execute(stmt)
    last_fight = result.scalar_one_or_none()

    if last_fight is not None:
        can_fight, hours = time_difference_check(last_fight.date_and_time, 6)
        if not can_fight:
            base_message = f'Вы не можете бросить вызов этому пользователю'
            raise CooldownNotElapsedError(base_message=base_message, hours=hours)


async def get_cards_participants(session_db: AsyncSession,
                                 attacker_card_id: int,
                                 protector_card_id: int
                                 ) -> dict[str, Card]:
    """ Возвращает карты участников с подгруженными амулетами.
        Args:
            session_db: сессия базы данных
            attacker_card_id: ID карты текущего пользователя
            protector_card_id: ID карты противника
        Returns:
            dict:
                - attacker_card: Card текущего пользователя
                - protector_card: Card противника
    """

    stmt = select(Card).where(
        Card.id.in_([attacker_card_id, protector_card_id])
    ).options(
        selectinload(Card.amulet).selectinload(AmuletItem.amulet_type),
        selectinload(Card.class_card),
        selectinload(Card.type_card),
        selectinload(Card.rarity_card)
    )

    result = await session_db.execute(stmt)
    cards = {card.id: card for card in result.scalars()}

    attacker_card = cards.get(attacker_card_id)
    protector_card = cards.get(protector_card_id)

    return {'attacker_card': attacker_card,
            'protector_card': protector_card}


async def stats_calculation(user_card: Card,
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


async def fight_now(user_card: Card,
                    enemy_card: Card
                    ) -> dict[str, Any]:
    """ Принимает сущности соперников и их карт и проводит бой.
        Если в битве есть победитель, то возвращает winner и loser,
        иначе user и enemy
        Args:
            user_card: Card текущего пользователя с амулетом, типом, классом и редкостью
            enemy_card: Card противника с амулетом, типом, классом и редкостью
        Returns:
            dict:
                - is_victory (bool): True, если есть победитель
                - winner (User | None): User, если есть победитель
                - loser (User | None): User, если есть победитель
                - history_fight (list[str]): история боя
    """

    answer_data = {'is_victory': None,
                   'winner': None,
                   'loser': None,
                   'history_fight': None}
    user_hp, user_damage, enemy_hp, enemy_damage = await stats_calculation(user_card, enemy_card)

    history_fight = []
    turn = 0
    winner = loser = None

    while True:
        # Ход пользователя
        user_hp, user_damage, enemy_hp, enemy_damage, history = process_turn(attacker_card=user_card,
                                                                             attacker_hp=user_hp,
                                                                             attacker_damage=user_damage,
                                                                             protector_card=enemy_card,
                                                                             protector_hp=enemy_hp,
                                                                             protector_damage=enemy_damage,
                                                                             turn_number=turn + 1
                                                                             )
        history_fight.append(history)
        if enemy_hp <= 0 or user_hp <= 0:
            break

        # Ход противника
        enemy_hp, enemy_damage, user_hp, user_damage, history = process_turn(attacker_card=enemy_card,
                                                                             attacker_hp=enemy_hp,
                                                                             attacker_damage=enemy_damage,
                                                                             protector_card=user_card,
                                                                             protector_hp=user_hp,
                                                                             protector_damage=user_damage,
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
        winner = enemy_card.owner
        loser = user_card.owner
        is_victory = False
    else:  # enemy_hp <= 0
        winner = user_card.owner
        loser = enemy_card.owner
        is_victory = True

    answer_data['is_victory'] = is_victory
    answer_data['winner'] = winner
    answer_data['loser'] = loser
    answer_data['history_fight'] = history_fight
    return answer_data


def process_turn(attacker_card: Card,
                 attacker_hp: float,
                 attacker_damage: float,
                 protector_card: Card,
                 protector_hp: float,
                 protector_damage: float,
                 turn_number: int
                 ) -> tuple[float, float, float, float, list[str]]:
    """ Обрабатывает один ход. Возвращает обновленные характеристики здоровья и урона,
        а также историю хода.
        Args:
            attacker_card: объект карты текущего пользователя
            attacker_hp: здоровье карты пользователя
            attacker_damage: урон карты пользователя
            protector_card: объект карты противника
            protector_hp: здоровье карты противника
            protector_damage: урон карты противника
            turn_number: номер хода
    """
    
    history = [f'Ход {turn_number} {attacker_card.owner.user.username}']
    # Способности защитника, срабатывающие до получения урона
    # Дриада (лечение защитника)
    if protector_card.class_card.name == 'Дриада':
        protector_hp, heal = use_spell_dryad(protector_card, protector_hp)
        history.append(formation_of_history(protector_card, heal))

    # Жнец (изменение урона атакующего и защитника)
    if attacker_card.class_card.name == 'Жнец':
        result = use_spell_reaper(attacker_card, attacker_damage, protector_damage)
        if result:
            attacker_damage, protector_damage, change = result
            history.append(formation_of_history(attacker_card, change))

    # Атака
    protector_hp = round(protector_hp - attacker_damage, 2)
    history.append(f'{attacker_card.owner.user.username} наносит {attacker_damage} урона')

    # Способности атакующего, срабатывающие после атаки
    if attacker_card.class_card.name == 'Берсерк':
        attacker_damage, change = use_spell_berserk(attacker_card, attacker_damage)
        history.append(formation_of_history(attacker_card, change))

    if attacker_card.class_card.name == 'Демон':
        result = use_spell_demon(attacker_card, attacker_damage, protector_hp)
        if result:
            protector_hp, add_damage = result
            history.append(formation_of_history(attacker_card, add_damage))

    if attacker_card.class_card.name == 'Оборотень':
        result = use_spell_werewolf(attacker_card, attacker_hp, attacker_damage)
        if result:
            attacker_hp, regen_hp = result
            history.append(formation_of_history(attacker_card, regen_hp))

    if protector_card.class_card.name == 'Призрак':  # Защитник уклоняется
        result = use_spell_ghost(protector_card, protector_hp, attacker_damage)
        if result:
            protector_hp, evade_damage = result
            history.append(formation_of_history(protector_card, evade_damage))

    if protector_card.class_card.name == 'Бог Император':  # Защитник отражает урон
        attacker_hp, return_damage = use_spell_emperor_mankind(protector_card, attacker_damage, attacker_hp)
        history.append(formation_of_history(protector_card, return_damage))

    history.append(f'Здоровье {attacker_card.owner.user.username} {attacker_hp}')
    history.append(f'Здоровье {protector_card.owner.user.username} {protector_hp}')

    return attacker_hp, attacker_damage, protector_hp, protector_damage, history


def use_spell_dryad(card: Card, card_hp: float) -> tuple[float, float]:
    """ Использование способности дриады.
        Восстанавливает свое здоровье в зависимости от уровня слияния.
        Возвращает итоговое количество своего здоровья и полученное лечение.
    """

    heal_hp = card.class_card.numeric_value + 5 * card.merger
    card_hp += heal_hp

    return card_hp, heal_hp


def use_spell_demon(card: Card, card_damage: float, enemy_card_hp: float) -> tuple[float, float] | None:
    """ Использование способности демона.
        Если сработал шанс, то наносит дополнительный урон, в зависимости от своей атаки и уровня слияния.
        Возвращает итоговое количество вражеского здоровья и дополнительный урон или None при неудаче.
    """

    chance = randint(1, 100)
    if chance <= card.class_card.chance_use:
        additional_damage = round(card_damage * (card.class_card.numeric_value + 5 * card.merger) / 100, 2)
        enemy_card_hp = round(enemy_card_hp - additional_damage, 2)

        return enemy_card_hp, additional_damage


def use_spell_werewolf(card: Card, card_hp: float, card_damage: float) -> tuple[float, float] | None:
    """ Использование способности оборотня.
        Если сработал шанс, то восстанавливает свое здоровье в зависимости от базового урона.
        Возвращает итоговое количество своего здоровья и количество восполненного здоровья или None при неудаче.
    """

    chance = randint(1, 100)
    if chance <= card.class_card.chance_use:
        regen_hp = round(card_damage * (card.class_card.numeric_value + 2 * card.merger) / 100, 2)
        card_hp = round(card_hp + regen_hp, 2)

        return card_hp, regen_hp


def use_spell_ghost(card: Card, card_hp: float, enemy_damage: float) -> tuple[float, float] | None:
    """ Использование способности призрака.
        Если сработал шанс, избегает урон от атаки противника (восполнятся здоровье)
        Возвращает итоговое количество своего здоровья или None при неудаче.
    """

    chance = randint(1, 100)
    if chance <= card.class_card.chance_use + 2.5 * card.merger:
        card_hp = round(card_hp + enemy_damage, 2)

        return card_hp, enemy_damage


def use_spell_emperor_mankind(card: Card, enemy_damage: float, enemy_hp: float) -> tuple[float, float]:
    """ Использование способности императора человечества.
        Наносит часть полученного урона атаковавшему.
        Возвращает итоговое количество здоровья нападающего, и количество возвращенного урона.
    """

    return_damage = round((card.class_card.numeric_value + 3 * card.merger) * enemy_damage / 100, 2)
    enemy_hp = round(enemy_hp - return_damage, 2)

    return enemy_hp, return_damage


def use_spell_berserk(card: Card, card_damage: float) -> tuple[float, float]:
    """ Использование способности берсерка.
        Увеличивает свой урон.
        Возвращает итоговое значение своего урона.
    """

    change = round(1 + 0.5 * card.merger, 2)
    up_damage = round(card_damage + change, 2)

    return up_damage, change


def use_spell_reaper(card: Card, card_damage: float, enemy_card_damage: float) -> tuple[float, float, float] | None:
    """ Использование способности жнеца.
        Если сработал шанс, понижает урон противника и повышает свой.
        Возвращает итоговые значения урона карты пользователя и карты противника или None при неудаче.
    """

    chance = randint(1, 100)
    if chance <= card.class_card.chance_use + 0.8 * card.merger:
        change = round(enemy_card_damage * (card.class_card.numeric_value + 2 * card.merger) / 100, 2)
        card_damage = round(card_damage + change, 2)
        enemy_card_damage = round(enemy_card_damage - change, 2)

        return card_damage, enemy_card_damage, change


def formation_of_history(card: Card, value: float) -> str:
    """ Создание текста для записи в историю ходов
        при использовании способности карты
    """

    description_move = (f'Используется способность {card.owner.user.username}-' +
                        f'{card.class_card.name} ' +
                        f'"{card.class_card.skill}" и ' +
                        f'{card.class_card.description_for_history_fight} ' +
                        f'{value}')

    return description_move
