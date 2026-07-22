from datetime import datetime
from pydantic import BaseModel

from cards_app.schemas.base import AmuletBase
from cards_app.schemas.cards import CardDTO


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
    result: str  # win, loss, draw
    user_card: CardBriefDTO
    opponent_id: int
    opponent_username: str
    opponent_card: CardBriefDTO


class ProfileBaseDTO(BaseModel):
    """ Базовая информация профиля (доступна всем) """

    id: int
    username: str
    about_user: str | None = None
    profile_pic: str | None = None
    win: int
    lose: int
    rating: int


class ProfileResponseDTO(BaseModel):
    """ Полный профиль для вывода на страницу.
        Разные данные для разных сценариев (неавторизованный гость, гость, владелец)
    """

    # Поля доступные всем
    profile: ProfileBaseDTO
    guild: GuildDTO | None = None
    card: CardDTO | None = None
    amulet: AmuletBase | None = None
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


class UserRatingTableDTO(BaseModel):
    """ Участник в таблице рейтинга """

    id: int
    username: str
    rating: int


class RatingTableDTO(BaseModel):
    """ Таблица рейтинга """

    user_rating: list[UserRatingTableDTO]
    total: int
    page: int
    size: int
    total_pages: int


class RecordTransaction(BaseModel):
    """ Запись в таблице транзакций """

    date_and_time: datetime
    before: int
    after: int
    comment: str
    delta: int


class TransactionsDTO(BaseModel):
    """ Транзакции пользователя """

    transactions: list[RecordTransaction] | None = None
