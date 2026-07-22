from pydantic import BaseModel


class AmuletDTO(BaseModel):
    """ Данные амулета, надетого на карту """

    id: int
    name: str
    bonus_hp: int
    bonus_damage: int


class CardDTO(BaseModel):
    """ Данные избранной карты пользователя """

    id: int
    class_card_name: str
    rarity_card_name: str
    type_card_name: str
    class_card_pic: str
    hp: float
    damage: float
    skill: str | None = None
    level: int
    max_level: int
    merger: int
    max_merger: int
    enhancement: int
    max_enhancement: int
    current_exp: int | None = None
    need_exp: int | None = None
    sale_status: bool | None = None
    price: int | None = None
    owner_id: int | None = None
    owner_username: str | None = None


class CardInfoDTO(BaseModel):
    """ Данные для просмотра карты """

    card: CardDTO
    amulet: AmuletDTO | None
    is_owner: bool = False


# class RarityCard(BaseModel):
#     """ Данные с шансом выпадения редкостей карты """
#
#     name: str
#     chance_drop: int
#
#
# class ClassCard(BaseModel):
#     """ Данные с классами карт, которые могут выпасть при бесплатном получении """
#
#     name: str
#     skill_description: str


# class GetFreeCardDTO(BaseModel):
#     """ Данные для страницы получения бесплатной карты """
#
#     all_classes: list[ClassCard]
#     all_rarities: list[RarityCard]
#     can_get_free_card: bool = False


class UserCardsDTO(BaseModel):
    """ Данные для просмотра всех карт пользователя """

    owner_id: int
    owner_username: str
    owner_current_card_id: int | None
    cards: list[CardDTO]


class CardsTradingDTO(BaseModel):
    """ Данные для просмотра торговой площадки """

    cards: list[CardDTO]


class OneCardForMergeDTO(BaseModel):
    """ Карты доступные для слияния """

    id: int
    class_card_name: str
    rarity_card_name: str
    type_card_name: str
    class_card_pic: str
    level: int
    max_level: int
    merger: int
    max_merger: int
    enhancement: int
    max_enhancement: int


class CardsForMergeDTO(BaseModel):
    """ Карты подходящие для слияния """

    current_card: OneCardForMergeDTO
    cards: list[OneCardForMergeDTO]
    need_cards: int
