from typing import TypedDict
from cards_app.models import *


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
