from pydantic import BaseModel
from typing import Optional, List


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
    skill: str
    level: int
    max_level: int
    merger: int
    max_merger: int
    enhancement: int
    max_enhancement: int
    current_exp: Optional[int] = None
    need_exp: Optional[int] = None


class CardInfoDTO(BaseModel):
    """ Данные для просмотра карты """

    card: CardDTO
    amulet: Optional[AmuletDTO]
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

    all_classes: List[ClassCard]
    all_rarities: List[RarityCard]
    can_get_free_card: bool = False
