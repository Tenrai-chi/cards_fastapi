from pydantic import BaseModel
from cards_app.schemas.base import AmuletBase, CardBase, ExpItemsBase


class ExpItemsInventoryDTO(ExpItemsBase):
    """ Данные о книгах опыта в инвентаре пользователя """

    rarity: str
    gold_for_use: int
    amount: int


class AmuletsInventoryDTO(AmuletBase):
    """ Данные об амулетах в инвентаре пользователя """

    # Карта, на которую надет амулет
    card_id: int | None
    card_class_name: str | None
    card_rarity_name: str | None

    # Амулет
    rarity_name: str
    image: str
    price_for_sale: int
    upgrades: int
    max_upgrade: int


class UpgradeItemsInventoryDTO(BaseModel):
    """ Данные о предметах усиления в инвентаре пользователя """

    id: int
    name: str
    description: str
    image: str
    gold_for_use: int
    amount: int


class FullInventoryDTO(BaseModel):
    """ Полный инвентарь пользователя """

    exp_items: list[ExpItemsInventoryDTO] | None
    amulets: list[AmuletsInventoryDTO] | None
    upgrade_items: list[UpgradeItemsInventoryDTO] | None
    count_amulet: int | None = None
    max_count_amulets: int | None = None


class CardLevelingDTO(CardBase):
    """ Информация о карте в меню увеличения уровня """

    level: int
    max_level: int
    current_exp: int
    need_exp: int


class FullInfoLevelingDTO(BaseModel):
    """ Информация для вывода на страницу с повышением уровня карты """

    card: CardLevelingDTO
    exp_items: list[ExpItemsInventoryDTO]


class CardUpgradingDTO(CardBase):
    """ Информация о карте в меню усиления """

    enhancement: int
    max_enhancement: int


class FullInfoUpgradingDTO(BaseModel):
    """ Информация для вывода на страницу с усилением карты """

    card: CardUpgradingDTO
    upgrade_items: list[UpgradeItemsInventoryDTO]
