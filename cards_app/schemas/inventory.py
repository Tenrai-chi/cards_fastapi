from pydantic import BaseModel


# class ExpItemsInventoryDTO(BaseModel):
#     """ Данные о книгах опыта в инвентаре пользователя """
#
#     name: str
#     rarity: str
#     experience_amount: int
#     image: str
#     gold_for_use: int
#     amount: int


# class AmuletsInventoryDTO(BaseModel):
#     """ Данные об амулетах в инвентаре пользователя """
#
#     # Карта, на которую надет амулет
#     card_id: int | None
#     card_class_name: str | None
#     card_rarity_name: str | None
#
#     # Амулет
#     id: int
#     name: str
#     rarity_name: str
#     bonus_hp: int
#     bonus_damage: int
#     image: str
#     price_for_sale: int
#     upgrades: int
#     max_upgrade: int


# class UpgradeItemsInventoryDTO(BaseModel):
#     """ Данные о предметах усиления в инвентаре пользователя """
#
#     id: int
#     name: str
#     description: str
#     image: str
#     gold_for_use: int
#     amount: int


# class FullInventoryDTO(BaseModel):
#     """ Полный инвентарь пользователя """
#
#     exp_items: list[ExpItemsInventoryDTO] | None
#     amulets: list[AmuletsInventoryDTO] | None
#     upgrade_items: list[UpgradeItemsInventoryDTO] | None
#     count_amulet: int | None = None
#     max_count_amulets: int | None = None


class CardLevelingDTO(BaseModel):
    """ Информация о карте в меню увеличения уровня """

    id: int
    class_name: str
    rarity_name: str
    type_name: str
    hp: int
    damage: int
    level: int
    max_level: int
    current_exp: int  # или float
    need_exp: int  # или float


# class FullInfoLevelingDTO(BaseModel):
#     """ Информация для вывода на страницу с повышением уровня карты """
#
#     card: CardLevelingDTO
#     exp_items: list[ExpItemsInventoryDTO]


# class CardUpgradingDTO(BaseModel):
#     """ Информация о карте в меню усиления """
#
#     id: int
#     class_name: str
#     rarity_name: str
#     type_name: str
#     hp: float
#     damage: float
#     image: str
#     enhancement: int
#     max_enhancement: int


# class FullInfoUpgradingDTO(BaseModel):
#     """ Информация для вывода на страницу с усилением карты """
#
#     card: CardUpgradingDTO
#     upgrade_items: list[UpgradeItemsInventoryDTO]
