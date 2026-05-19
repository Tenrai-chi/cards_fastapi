from pydantic import BaseModel


class CardInStoreDTO(BaseModel):
    """ Данные амулета, надетого на карту """

    id: int
    class_card_name: str
    rarity_card_name: str
    type_card_name: str
    class_card_pic: str
    hp: float
    damage: float
    price: int
    discount: int
    discount_now: bool


class CardStoreDTO(BaseModel):
    """ Данные избранной карты пользователя """

    cards: list[CardInStoreDTO]
