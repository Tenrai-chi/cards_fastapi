from pydantic import BaseModel
from .base import CardBase, AmuletBase


class CardDTO(CardBase):
    """ Полные данные карты пользователя (для профиля, торговли и т.д.) """

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


# class OneCardForMergeDTO(CardBase):
#     """ Урезанная версия карты для страницы слияния """
#
#     level: int
#     max_level: int
#     merger: int
#     max_merger: int
#     enhancement: int
#     max_enhancement: int
#
#
class CardInfoDTO(BaseModel):
    """ Данные для просмотра карты """

    card: CardDTO
    amulet: AmuletBase | None
    is_owner: bool = False


class RarityCard(BaseModel):
    """ Данные с шансом выпадения редкостей карты """

    name: str
    chance_drop: int


class ClassCard(BaseModel):
    """ Данные с классами карт, которые могут выпасть при бесплатном получении """

    name: str
    skill_description: str


class GetFreeCardDTO(BaseModel):
    """ Данные для страницы получения бесплатной карты """

    all_classes: list[ClassCard]
    all_rarities: list[RarityCard]
    can_get_free_card: bool = False


class UserCardsDTO(BaseModel):
    """ Данные для просмотра всех карт пользователя """

    owner_id: int
    owner_username: str
    owner_current_card_id: int | None
    cards: list[CardDTO]


class CardsTradingDTO(BaseModel):
    """ Данные для просмотра торговой площадки """

    cards: list[CardDTO]
#
#
# class CardsForMergeDTO(BaseModel):
#     """ Карты, подходящие для слияния """
#
#     current_card: OneCardForMergeDTO
#     cards: list[OneCardForMergeDTO]
#     need_cards: int

