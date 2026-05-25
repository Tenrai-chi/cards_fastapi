from typing import TypedDict
from cards_app.schemas import *


class ViewCardUseCaseDict(TypedDict):
    """ Кастомный словарь для возврата данных из ViewCardUseCase """

    card_info_dto: CardInfoDTO | None
    error_message: str | None
    status_code: int


class ViewGetFreeCardUseCaseDict(TypedDict):
    """ Кастомный словарь для возврата данных из ViewGetFreeCardUseCase """

    get_free_card_dto: GetFreeCardDTO | None
    status_code: int


class GetFreeCardUseCaseDict(TypedDict):
    """ Кастомный словарь для возврата данных из GetFreeCardUseCase """

    success: bool
    new_card_id: int | None
    error_message: str | None
    status_code: int


class ViewNewsUseCaseDict(TypedDict):
    """ Кастомный словарь для возврата данных из ViewNewsUseCase """

    news_dto: NewsDTO | None
    status_code: int


class ViewStartEventUseCaseDict(TypedDict):
    """ Кастомный словарь для возврата данных из ViewStartEventUseCase """

    start_event_awards_dto: StartEventAwardsDTO | None
    status_code: int


class GetAwardStartEventUseCaseDict(TypedDict):
    """ Кастомный словарь для возврата данных из GetAwardStartEventUseCase """

    success_message: str | None
    error_message: str | None
    new_card_id: int | None
    status_code: int


class ViewProfileUseCaseDict(TypedDict):
    """ Кастомный словарь для возврата данных из ViewProfileUseCase """

    user_info: ProfileResponseDTO | None
    error_message: str | None
    status_code: int


class AddFavoriteUserUseCaseDict(TypedDict):
    """ Кастомный словарь для возврата данных из AddFavoriteUserUseCase """

    success: bool
    error_message: str | None
    status_code: int
    success_message: str | None


class RemoveFavoriteUserUseCaseDict(TypedDict):
    """ Кастомный словарь для возврата данных из RemoveFavoriteUserUseCase """

    success: bool
    error_message: str | None
    status_code: int
    success_message: str | None


class FavoriteUsersUseCaseDict(TypedDict):
    """ Кастомный словарь для возврата данных из FavoriteUsersUseCase """

    favorite_users_dto: FavoriteUsersPageDTO | None
    error_message: str | None
    status_code: int


class ViewCardStoreUseCaseDict(TypedDict):
    """ Кастомный словарь для возврата данных из ViewCardStoreUseCase """

    card_store_dto: CardStoreDTO | None
    status_code: int


class BuyStoreCardUseCaseDict(TypedDict):
    """ Кастомный словарь для возврата данных из BuyStoreCardUseCase """

    success: bool
    error_message: str | None
    new_card_id: int | None
    status_code: int


class ProcessFightUseCaseDict(TypedDict):
    """ Кастомный словарь для возврата данных из ProcessFightUseCase """
    # todo в процессе

    fight_dto: FightDTO | None
    error_message: str | None
    status_code: int
