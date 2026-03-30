from pydantic import BaseModel
from datetime import datetime


class UserOut(BaseModel):
    id: int
    username: str
    email: str
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
