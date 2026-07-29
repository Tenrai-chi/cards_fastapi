from pydantic import BaseModel

from cards_app.schemas.base import CardBase, AmuletBase, ExpItemsBase


class CardInStoreDTO(CardBase):
    """ Данные карты из магазина """

    price: int
    discount: int
    discount_now: bool


class CardStoreDTO(BaseModel):
    """ Список карт в магазине карт"""

    cards: list[CardInStoreDTO]


class BoxStoreDTO(BaseModel):
    """ Сундуки  """

    id: int
    name: str
    description: str
    price: int
    image: str


class ExpItemsStoreDTO(ExpItemsBase):
    """ Книги опыта """

    id: int
    price: int
    sale_now: bool


class AmuletsStoreDTO(AmuletBase):
    """ Амулеты """

    price: int
    image: str
    discount: int
    discount_now: bool
    rarity_name: str


class UpgradeItemsStoreDTO(BaseModel):
    """ Предметы усиления """

    id: int
    name: str
    description: str
    image: str
    price: int


class AllStoreDTO(BaseModel):
    """ Весь ассортимент магазина предметов """

    boxes: list[BoxStoreDTO] | None
    exp_items: list[ExpItemsStoreDTO] | None
    amulets: list[AmuletsStoreDTO] | None
    upgrade_items: list[UpgradeItemsStoreDTO] | None


class AmuletRewardDTO(AmuletBase):
    """ Амулет в открытом сундуке """

    image: str
    rarity_name: str
