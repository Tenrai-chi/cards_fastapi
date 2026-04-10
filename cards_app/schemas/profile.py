from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

from cards_app.schemas.cards import AmuletDTO, CardDTO


class GuildDTO(BaseModel):
    """ Данные гильдии """

    id: int
    name: str


class CardBriefDTO(BaseModel):
    """ Информация о карте в истории боев """

    id: int
    class_name: str
    type_name: str


class FightHistoryRecordDTO(BaseModel):
    """ История боев """

    date_and_time: datetime
    result: str
    user_card: CardBriefDTO
    opponent_profile_id: int
    opponent_username: str
    opponent_card: CardBriefDTO


class ProfileBaseDTO(BaseModel):
    """ Базовая информация профиля (доступна всем) """

    id: int
    username: str
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
    role: Optional[str] = 'anonymous'

    # Владелец
    user_email: Optional[str] = None
    battle_history: Optional[List[FightHistoryRecordDTO]] = None

    # Гость
    win_vs: Optional[int] = None
    lose_vs: Optional[int] = None
    is_favorite: Optional[bool] = None


class FavoriteUserDTO(BaseModel):
    """ Избранный пользователь """

    id: int
    username: str


class FavoriteUsersPageDTO(BaseModel):
    """ Информация для страницы просмотра избранных пользователей """

    amount_users: int
    max_amount_users: int
    favorite_users: Optional[List[FavoriteUserDTO]]
