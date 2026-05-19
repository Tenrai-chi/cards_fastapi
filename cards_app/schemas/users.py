from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    is_staff: bool
    is_superuser: bool
    last_login: datetime | None
    date_joined: datetime
    first_name: str | None
    last_name: str | None
    email_verified: bool

    class Config:
        from_attributes = True


class CurrentUserForMenuDTO(BaseModel):
    """ Данные для вывода информации в шапке профиля """

    id: int | None = None
    username: str | None = None
    gold: int | None = None
    diamond: int | None = None
