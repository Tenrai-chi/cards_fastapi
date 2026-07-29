from datetime import datetime
from pydantic import BaseModel

from cards_app.schemas.base import GuildBase, AmuletBase, CardBase, ProfileBase
from cards_app.schemas.cards import CardDTO


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


class FavoriteUserDTO(BaseModel):
    """ Избранный пользователь """

    id: int
    username: str


class FavoriteUsersPageDTO(BaseModel):
    """ Информация для страницы просмотра избранных пользователей """

    amount_users: int
    max_amount_users: int
    favorite_users: list[FavoriteUserDTO]


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


class FightHistoryRecordDTO(BaseModel):
    """ История боев """

    date_and_time: datetime
    result: str  # win, loss, draw
    user_card: CardBase
    opponent_id: int
    opponent_username: str
    opponent_card: CardBase


class ProfileFullInfoDTO(ProfileBase):
    """ Полный профиль для вывода на страницу.
        Разные данные для разных сценариев (неавторизованный гость, гость, владелец)
    """

    # Поля доступные всем
    guild: GuildBase | None = None
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
