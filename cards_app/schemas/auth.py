from pydantic import BaseModel, EmailStr


# todo почитать как лучше использовать при регистрации и тд
class UserRegister(BaseModel):

    username: str
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class RefreshTokenRequest(BaseModel):
    refresh_token: str
