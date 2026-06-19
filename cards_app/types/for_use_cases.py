from typing import TypedDict
from cards_app.schemas import (AllStoreDTO, UserCardsDTO, CardsTradingDTO, TransactionsDTO,
                               CardInfoDTO, GetFreeCardDTO, NewsDTO, StartEventAwardsDTO,
                               ProfileResponseDTO, RatingTableDTO, FavoriteUsersPageDTO,
                               CardStoreDTO, FightDTO, FullInventoryDTO, FullInfoLevelingDTO, CardsForMergeDTO,
                               OpenBoxExpItemDTO, OpenBoxAmuletDTO, FullInfoUpgradingDTO, CurrentUserForMenuDTO)


class BaseUseCaseDict(TypedDict):
    """ Базовый класс для всех словарей use case """

    status_code: int


class ErrorMixin(TypedDict):
    """ Миксин для словарей, которые могут содержать сообщение об ошибке.
        Используется в use case, где возможна ошибка, требующая пояснения пользователю
    """

    error_message: str | None


class ErrorWithUserMixin(ErrorMixin):
    """ Миксин для словарей, которые должны содержать информацию о пользователе при ошибке.
        Используется в use case, где возможна ошибка, требующая пояснения пользователю
        и информации о профиле для вывода в шапку сайта.
        Должен использоваться при статус-кодах: 400, 404, 500
    """

    current_user_dto: CurrentUserForMenuDTO | None


class SuccessMessageMixin(TypedDict):
    """ Миксин для словарей, которые могут содержать сообщение об успехе.
        Используется в use case, где необходимо передать пользователю сообщение об успехе
    """

    success_message: str | None


class SuccessMixin(TypedDict):
    """ Миксин для словарей с флагом успеха операции.
        Используется в use case, где необходимо явно указывать успех/неудачу
    """

    success: bool


class ViewCardUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из ViewCardUseCase """

    card_info_dto: CardInfoDTO | None


class ViewGetFreeCardUseCaseDict(BaseUseCaseDict):
    """ Кастомный словарь для возврата данных из ViewGetFreeCardUseCase """

    get_free_card_dto: GetFreeCardDTO | None


class GetFreeCardUseCaseDict(BaseUseCaseDict, ErrorWithUserMixin, SuccessMixin):
    """ Кастомный словарь для возврата данных из GetFreeCardUseCase """

    new_card_id: int | None


class ViewNewsUseCaseDict(BaseUseCaseDict):
    """ Кастомный словарь для возврата данных из ViewNewsUseCase """

    news_dto: NewsDTO | None


class ViewStartEventUseCaseDict(BaseUseCaseDict):
    """ Кастомный словарь для возврата данных из ViewStartEventUseCase """

    start_event_awards_dto: StartEventAwardsDTO | None


class GetAwardStartEventUseCaseDict(BaseUseCaseDict, ErrorWithUserMixin, SuccessMessageMixin):
    """ Кастомный словарь для возврата данных из GetAwardStartEventUseCase """

    new_card_id: int | None


class ViewProfileUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из ViewProfileUseCase """

    user_info: ProfileResponseDTO | None


class AddFavoriteUserUseCaseDict(BaseUseCaseDict, ErrorMixin, SuccessMixin, SuccessMessageMixin):
    """ Кастомный словарь для возврата данных из AddFavoriteUserUseCase """


class RemoveFavoriteUserUseCaseDict(BaseUseCaseDict, ErrorMixin, SuccessMixin, SuccessMessageMixin):
    """ Кастомный словарь для возврата данных из RemoveFavoriteUserUseCase """


class FavoriteUsersUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из FavoriteUsersUseCase """

    favorite_users_dto: FavoriteUsersPageDTO | None


class ViewCardStoreUseCaseDict(BaseUseCaseDict):
    """ Кастомный словарь для возврата данных из ViewCardStoreUseCase """

    card_store_dto: CardStoreDTO | None


class BuyStoreCardUseCaseDict(BaseUseCaseDict, ErrorMixin, SuccessMixin):
    """ Кастомный словарь для возврата данных из BuyStoreCardUseCase """

    new_card_id: int | None


class ProcessFightUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из ProcessFightUseCase """

    fight_dto: FightDTO | None


class ViewUsersRatingDict(BaseUseCaseDict):
    """ Кастомный словарь для возврата данных из ViewUsersRatingUseCase """

    rating_dto: RatingTableDTO


class ViewItemStoreUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из ViewUsersRatingUseCase """

    store_dto: AllStoreDTO | None


class ViewUserCardsUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из ViewUserCardsUseCase """

    user_cards_dto: UserCardsDTO | None


class ViewTradingUseCaseDict(BaseUseCaseDict):
    """ Кастомный словарь для возврата данных из ViewTradingUseCase """

    cards_trading_dto: CardsTradingDTO | None


class UserTransactionsUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из UserTransactionsUseCase """

    transactions_dto: TransactionsDTO | None


class ViewInventoryUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из ViewInventoryUseCase """

    inventory_dto: FullInventoryDTO | None


class ViewLevelUpUseCaseDict(BaseUseCaseDict):
    """ Кастомный словарь для возврата данных из ViewLevelUpUseCase """

    info_leveling_dto: FullInfoLevelingDTO | None


class SaleAmuletUseCaseDict(BaseUseCaseDict, ErrorWithUserMixin, SuccessMixin, SuccessMessageMixin):
    """ Кастомный словарь для возврата данных из SaleAmuletUseCase """


class ViewMergeUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из ViewMergeUseCase """

    merge_dto: CardsForMergeDTO | None


class ViewUpgradeUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из ViewUpgradeUseCase """

    upgrade_dto: FullInfoUpgradingDTO | None


class MergeUseCaseDict(BaseUseCaseDict, ErrorWithUserMixin, SuccessMixin, SuccessMessageMixin):
    """ Кастомный словарь для возврата данных из MergeUseCase """


class UpgradeUseCaseDict(BaseUseCaseDict, ErrorWithUserMixin, SuccessMixin, SuccessMessageMixin):
    """ Кастомный словарь для возврата данных из MergeUseCase """


class BuyBoxUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из BuyBoxUseCase """

    exp_items_dto: OpenBoxExpItemDTO | None
    amulets_items_dto: OpenBoxAmuletDTO | None
    card_id: int | None


class BuyItemUseCaseDict(BaseUseCaseDict, ErrorMixin, SuccessMixin, SuccessMessageMixin):
    """ Кастомный словарь для возврата данных
        из BuyExpItemUseCase, BuyAmuletUseCase, BuyUpgradeItemUseCase
    """
