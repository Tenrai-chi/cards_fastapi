from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class GuildDTO(BaseModel):
    """ Данные гильдии """

    id: int
    name: str


class AmuletDTO(BaseModel):
    """ Данные амулета, надетого на карту """

    id: int
    name: str
    bonus_hp: int
    bonus_damage: int


class CardDTO(BaseModel):
    """ Данные избранной карты пользователя """

    id: int
    class_card_name: str
    rarity_card_name: str
    type_card_name: str
    class_card_pic: str
    hp: float
    damage: float
    skill: str
    level: int
    max_level: int
    merger: int
    max_merger: int
    enhancement: int
    max_enhancement: int


class CardBriefDTO(BaseModel):
    id: int
    class_name: str
    type_name: str


class FightHistoryRecordDTO(BaseModel):
    date_and_time: datetime
    result: str
    user_card: CardBriefDTO
    opponent_profile_id: int
    opponent_username: str
    opponent_card: CardBriefDTO


class ProfileBaseDTO(BaseModel):
    """ Базовая информация профиля (доступна всем) """

    about_user: Optional[str] = None
    profile_pic: str
    win: int
    lose: int


class ProfileResponseDTO(BaseModel):
    """ Полный профиль для вывода на страницу.
        Разные данные для разных сценариев (неавторизованный гость, гость, владелец)
    """

    # Поля доступные всем
    profile: ProfileBaseDTO
    guild: Optional[GuildDTO] = None
    card: Optional[CardDTO] = None
    amulet: Optional[AmuletDTO] = None
    role: Optional[str] = 'Anonim'

    # Владелец
    user_email: Optional[str] = None
    battle_history: Optional[List[FightHistoryRecordDTO]] = None

    # Гость
    win_vs: Optional[int] = None
    lose_vs: Optional[int] = None
    is_favorite: Optional[bool] = None
