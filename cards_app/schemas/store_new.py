from pydantic import BaseModel

from cards_app.schemas.base import CardBase


class CardInStoreDTO(CardBase):
    """ Данные карты из магазина """

    price: int
    discount: int
    discount_now: bool


class CardStoreDTO(BaseModel):
    """ Список карт в магазине карт"""

    cards: list[CardInStoreDTO]