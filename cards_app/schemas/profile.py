from datetime import datetime
from pydantic import BaseModel

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
    about_user: str | None = None
    profile_pic: str
    win: int
    lose: int


class ProfileResponseDTO(BaseModel):
    """ Полный профиль для вывода на страницу.
        Разные данные для разных сценариев (неавторизованный гость, гость, владелец)
    """

    # Поля доступные всем
    profile: ProfileBaseDTO
    guild: GuildDTO | None = None
    card: CardDTO | None = None
    amulet: AmuletDTO | None = None
    role: str | None = 'anonymous'

    # Владелец
    user_email: str | None = None
    battle_history: list[FightHistoryRecordDTO] | None = None

    # Гость
    win_vs: int | None = None
    lose_vs: int | None = None
    is_favorite: bool | None = None


class FavoriteUserDTO(BaseModel):
    """ Избранный пользователь """

    id: int
    username: str


class FavoriteUsersPageDTO(BaseModel):
    """ Информация для страницы просмотра избранных пользователей """

    amount_users: int
    max_amount_users: int
    favorite_users: list[FavoriteUserDTO]
