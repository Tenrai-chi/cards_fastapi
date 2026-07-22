from .base import (
    UseCaseResponse, ErrorMessageMixin, CurrentUserMixin, SuccessFlagMixin
)

from .cards_new import (
    CardInfoDTO, GetFreeCardDTO, UserCardsDTO, CardsTradingDTO
)


# -------- Ответы в USE CASES --------
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
