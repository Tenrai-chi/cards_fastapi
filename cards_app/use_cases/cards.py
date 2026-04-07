from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.config.exceptions import CardNotFoundError
from cards_app.services.cards import get_card_with_details, get_drop_chance_card
from cards_app.schemas.cards import AmuletDTO, CardInfoDTO, CardDTO, GetFreeCardDTO, RarityCard, ClassCard
from cards_app.utils.common import calculate_need_exp
from cards_app.models.users import User


class ViewCardUseCase:
    """ Use case для просмотра карты.
        Преобразовывает данные для вывода информации о карте
        Если карты нет, то выбрасывает CardNotFoundError
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self,
                      card_id: int,
                      current_user: User
                      ) -> CardInfoDTO:

        card = await get_card_with_details(self.session_db, card_id)
        if not card:
            raise CardNotFoundError()

        need_exp = calculate_need_exp(card.level)
        amulet_dto = None
        card_dto = CardDTO(id=card.id,
                           class_card_name=card.class_card.name,
                           rarity_card_name=card.rarity_card.name,
                           type_card_name=card.type_card.name,
                           class_card_pic=card.class_card.image,
                           hp=card.hp,
                           damage=card.damage,
                           skill=card.class_card.skill,
                           level=card.level,
                           max_level=card.rarity_card.max_level,
                           merger=card.merger,
                           max_merger=card.max_merger,
                           enhancement=card.enhancement,
                           max_enhancement=card.max_enhancement,
                           current_exp=card.experience_bar,
                           need_exp=need_exp)
        if card.amulet:
            amulet_dto = AmuletDTO(id=card.amulet.id,
                                   name=card.amulet.amulet_type.name,
                                   bonus_hp=card.amulet.amulet_type.bonus_hp,
                                   bonus_damage=card.amulet.amulet_type.bonus_damage,
                                   )
        if current_user:
            is_owner = True if current_user.profile.id == card.owner_id else False
        else:
            is_owner = False

        return CardInfoDTO(card=card_dto,
                           amulet=amulet_dto,
                           is_owner=is_owner
                           )


class ViewGetFreeCard:
    """ Use case для просмотра страницы с получением бесплатной карты """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self) -> GetFreeCardDTO:
        data_for_page: dict = await get_drop_chance_card(self.session_db)
        all_classes = data_for_page['classes']
        all_rarities = data_for_page['rarities']

        classes_card = []
        rarities_card = []
        for class_card in all_classes:
            classes_card.append(ClassCard(name=class_card.name,
                                          skill_description=class_card.description))

        for rarity_card in all_rarities:
            rarities_card.append(RarityCard(name=rarity_card.name,
                                            chance_drop=rarity_card.drop_chance))

        return GetFreeCardDTO(all_classes=classes_card,
                              all_rarities=rarities_card)

