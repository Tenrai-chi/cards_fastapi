from sqlalchemy.ext.asyncio import AsyncSession
from cards_app.schemas.store import CardInStoreDTO, CardStoreDTO
from cards_app.services.store import get_cards_in_store


class ViewCardStoreUseCase:
    """ Use case для просмотра магазина карт.
        Преобразовывает данные для вывода информации о продаваемых картах.
    """

    def __init__(self, session_db: AsyncSession):
        self.session_db = session_db

    async def execute(self) -> CardStoreDTO:
        all_cards: list = await get_cards_in_store(session_db=self.session_db)
        cards_in_store = []
        for card in all_cards:
            cards_in_store.append(CardInStoreDTO(id=card.id,
                                                 class_card_name=card.class_card.name,
                                                 rarity_card_name=card.rarity_card.name,
                                                 type_card_name=card.type_card.name,
                                                 class_card_pic=card.class_card.image,
                                                 hp=card.hp,
                                                 damage=card.damage,
                                                 price=card.price,
                                                 discount=card.discount,
                                                 discount_now=card.discount_now
                                                 )
                                  )

        return CardStoreDTO(cards=cards_in_store)

