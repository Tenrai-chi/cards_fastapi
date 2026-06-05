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


class BoxStoreDTO(BaseModel):
    """ Сундуки  """

    id: int
    name: str
    description: str
    price: int
    image: str


class ExpItemsStoreDTO(BaseModel):
    """ Книги опыта """

    id: int
    name: str
    experience_amount: int
    price: int
    image: str
    sale_now: bool


class AmuletsStoreDTO(BaseModel):
    """ Амулеты """

    id: int
    name: str
    bonus_hp: float
    bonus_damage: float
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


class ExpItemRewardDTO(BaseModel):
    """ Информация о книге полученной из сундука """

    name: str
    experience_amount: int
    image: str


class AmuletRewardDTO(BaseModel):
    """ Информация об амулете полученном из сундука """

    name: str
    bonus_hp: float
    bonus_damage: float
    image: str
    rarity_name: str


class OpenBoxAmuletDTO(BaseModel):
    """ Вывод наград из сундуков амулетов """

    amulets: list[AmuletRewardDTO]


class OpenBoxExpItemDTO(BaseModel):
    """ Вывод наград из сундуков предметов опыта """

    boxs: list[ExpItemRewardDTO]
