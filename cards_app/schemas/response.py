from .base import (
    UseCaseResponse, ErrorMessageMixin, CurrentUserMixin, SuccessFlagMixin
)
from .cards_new import (CardInfoDTO, AmuletBase)


# -------- Ответы в USE CASES --------
class ViewCardUseCaseResponse(UseCaseResponse, ErrorMessageMixin):
    """ Ответ для просмотра одной карты """

    card_info: CardInfoDTO | None = None
