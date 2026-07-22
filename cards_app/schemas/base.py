from pydantic import BaseModel


# -------- Общие схемы ответов --------
class UseCaseResponse(BaseModel):
    """ Базовый ответ любого use case """

    status_code: int


class SuccessFlagMixin(BaseModel):
    """
    Миксин для схем, которые могут содержать сообщение об успехе.
    Используется в use case, где необходимо передать пользователю сообщение об успехе.
    """

    success: bool


class ErrorMessageMixin(BaseModel):
    """
    Миксин для схем, которые могут содержать сообщения об ошибке.
    Используется в use case, где возможна ошибка, требующая пояснения пользователю.
    """

    error_message: str | None = None


class SuccessMessageMixin(BaseModel):
    """
    Миксин для схем, которые могут содержать сообщение об успехе.
    Используется в use case, где необходимо передать пользователю сообщение об успехе.
    """

    success_message: str | None = None


class CurrentUserMixin(BaseModel):
    """ Данные для вывода информации в шапке профиля.
        Используется в схемах, где необходимо возвращать информацию о текущем пользователе.
    """

    id: int | None = None
    username: str | None = None
    gold: int | None = None
    diamond: int | None = None


# -------- Схемы сущностей --------
class CardBase(BaseModel):
    """ Базовая схема для любой карты"""

    id: int
    class_card_name: str
    rarity_card_name: str
    type_card_name: str
    class_card_pic: str
    hp: float
    damage: float


class AmuletBase(BaseModel):
    """ Базовая схема для амулетов """

    id: int
    name: str
    bonus_hp: int
    bonus_damage: int

