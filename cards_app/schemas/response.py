from .base import (
    UseCaseResponse, ErrorMessageMixin,
)
from .cards_new import (CardInfoDTO, GetFreeCardDTO)


# -------- Ответы в USE CASES --------
class ViewCardUseCaseResponse(UseCaseResponse, ErrorMessageMixin):
    """ Ответ для просмотра одной карты """

    card_info: CardInfoDTO | None = None


class ViewGetFreeCardUseCaseResponse(UseCaseResponse):
    """ Ответ для просмотра страницы с получением случайной карты """

    get_free_card: GetFreeCardDTO | None
