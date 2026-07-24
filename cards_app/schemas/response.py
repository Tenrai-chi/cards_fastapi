from cards_app.schemas.base import UseCaseResponse, ErrorMessageMixin, CurrentUserMixin, SuccessFlagMixin, SuccessMessageMixin
from cards_app.schemas.cards import CardInfoDTO, GetFreeCardDTO, UserCardsDTO, CardsTradingDTO, CardsForMergeDTO
from cards_app.schemas.inventory_new import FullInfoUpgradingDTO
from cards_app.schemas.news import NewsDTO
from cards_app.schemas.profile import RatingTableDTO


# -------- Cards --------
class ViewCardUseCaseResponse(UseCaseResponse, ErrorMessageMixin):
    """ Ответ для просмотра одной карты """

    card_info: CardInfoDTO | None = None


class ViewGetFreeCardUseCaseResponse(UseCaseResponse):
    """ Ответ для просмотра страницы с получением случайной карты """

    get_free_card: GetFreeCardDTO | None


class GetFreeCardUseCaseResponse(UseCaseResponse, CurrentUserMixin, SuccessFlagMixin, ErrorMessageMixin):
    """ Ответ для получения бесплатной карты """

    new_card_id: int | None


class ViewUserCardsUseResponse(UseCaseResponse, ErrorMessageMixin):
    """ Ответ для получения всех карт пользователя """

    user_cards: UserCardsDTO | None


class ViewTradingUseCaseResponse(UseCaseResponse):
    """ Ответ для получения всех карт, выставленных на продажу игроками """

    cards_trading: CardsTradingDTO | None


class ViewMergeUseCaseResponse(UseCaseResponse, ErrorMessageMixin):
    """ Ответ для получения списка карт, доступных для слияния """

    merge: CardsForMergeDTO | None


class MergeUseCaseResponse(UseCaseResponse, ErrorMessageMixin, CurrentUserMixin, SuccessFlagMixin, SuccessMessageMixin):
    """ Ответ на запрос слить карты. Пустой, потому что все данные наследуются из миксин. """


class ViewUpgradeUseCaseResponse(UseCaseResponse, ErrorMessageMixin):
    """ Ответ на получение карты и предметов для ее усиления """

    upgrade_info: FullInfoUpgradingDTO | None


class UpgradeUseCaseResponse(UseCaseResponse, CurrentUserMixin, SuccessMessageMixin, ErrorMessageMixin):
    """ Ответ на запрос усилить карту с помощью предметов усиления """


# -------- Events --------
class ViewNewsUseCaseResponse(UseCaseResponse):
    """ Ответ на запрос получить новости сайта """

    news: NewsDTO | None


class ViewUsersRatingResponse(UseCaseResponse):
    """ Ответ на запрос получения таблицы рейтинга """

    rating: RatingTableDTO | None

