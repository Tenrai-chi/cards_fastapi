from typing import TypedDict
from cards_app.schemas.fight import FightDTO
from cards_app.schemas.profile import ProfileResponseDTO, FavoriteUsersPageDTO, TransactionsDTO
from cards_app.schemas.users import CurrentUserForMenuDTO


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


# ------- todo ПЕРЕДЕЛАТЬ и удалить -----------
class GetFreeCardUseCaseDict(BaseUseCaseDict, ErrorWithUserMixin, SuccessMixin):
    """ Кастомный словарь для возврата данных из GetFreeCardUseCase """

    new_card_id: int | None


class GetAwardStartEventUseCaseDict(BaseUseCaseDict, ErrorWithUserMixin, SuccessMessageMixin):
    """ Кастомный словарь для возврата данных из GetAwardStartEventUseCase """

    new_card_id: int | None


class ViewProfileUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из ViewProfileUseCase """

    user_info: ProfileResponseDTO | None


class AddFavoriteUserUseCaseDict(BaseUseCaseDict, ErrorWithUserMixin, SuccessMixin, SuccessMessageMixin):
    """ Кастомный словарь для возврата данных из AddFavoriteUserUseCase """


class RemoveFavoriteUserUseCaseDict(BaseUseCaseDict, ErrorWithUserMixin, SuccessMixin, SuccessMessageMixin):
    """ Кастомный словарь для возврата данных из RemoveFavoriteUserUseCase """


class FavoriteUsersUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из FavoriteUsersUseCase """

    favorite_users_dto: FavoriteUsersPageDTO | None


# class BuyStoreCardUseCaseDict(BaseUseCaseDict, ErrorWithUserMixin, SuccessMixin):
#     """ Кастомный словарь для возврата данных из BuyStoreCardUseCase """
#
#     new_card_id: int | None


class ProcessFightUseCaseDict(BaseUseCaseDict, ErrorWithUserMixin):
    """ Кастомный словарь для возврата данных из ProcessFightUseCase """

    fight_dto: FightDTO | None


# class ViewItemStoreUseCaseDict(BaseUseCaseDict, ErrorMixin):
#     """ Кастомный словарь для возврата данных из ViewUsersRatingUseCase """
#
#     store_dto: AllStoreDTO | None


class UserTransactionsUseCaseDict(BaseUseCaseDict, ErrorMixin):
    """ Кастомный словарь для возврата данных из UserTransactionsUseCase """

    transactions_dto: TransactionsDTO | None

#
# class BuyBoxUseCaseDict(BaseUseCaseDict, ErrorWithUserMixin):
#     """ Кастомный словарь для возврата данных из BuyBoxUseCase """
#
#     exp_items_dto: OpenBoxExpItemDTO | None
#     amulets_items_dto: OpenBoxAmuletDTO | None
#     card_id: int | None


class BuyItemUseCaseDict(BaseUseCaseDict, ErrorWithUserMixin, SuccessMixin, SuccessMessageMixin):
    """ Кастомный словарь для возврата данных
        из BuyExpItemUseCase, BuyAmuletUseCase, BuyUpgradeItemUseCase
    """
