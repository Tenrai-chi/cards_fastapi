from pydantic import BaseModel
from typing import List, Optional


class StartEventAwardDTO(BaseModel):
    """ Награда дня """

    day: int
    type_award: str
    amount_or_rarity: str
    description: Optional[str] = None


class StartEventAwardsDTO(BaseModel):
    """ Просмотр наград стартового события """

    awards: List[StartEventAwardDTO]
    can_get_award: bool
    received: int
