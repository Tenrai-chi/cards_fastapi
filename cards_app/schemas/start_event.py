from pydantic import BaseModel


class StartEventAwardDTO(BaseModel):
    """ Награда дня """

    day: int
    type_award: str
    amount_or_rarity: str
    description: str | None = None


class StartEventAwardsDTO(BaseModel):
    """ Просмотр наград стартового события """

    awards: list[StartEventAwardDTO]
    can_get_award: bool
    received: int
