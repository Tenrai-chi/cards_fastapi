from typing import TypedDict
from cards_app.models import *
from cards_app.schemas import *
from cards_app.schemas.cards import RarityCard


class RaritiesAndClassesDict(TypedDict):
    """ Кастомный словарь для вывода информации о редкостях и классах карт """

    rarities: list[Rarity]
    classes: list[ClassCard]


class FightNowDataDict(TypedDict):
    """ Кастомный словарь для вывода информации о прошедшей битве между 2 пользователями """

    is_victory: bool
    winner: User | None
    loser: User | None
    history_fight: list[list[str]]


class AddGoldForFightDict(TypedDict):
    """ Кастомный словарь для вывода информации о полученном золоте после битвы """

    gold_before: int
    gold_after: int
    comment: str


class RewardLootAfterFightDict(TypedDict):
    """ Кастомный словарь для вывода полученных наград после битвы """

    exp_items: list[ExperienceItems] | list
    amulets: list[AmuletType] | list
