from pydantic import BaseModel
from datetime import datetime


class NewsRecordDTO(BaseModel):
    """ Новость """

    title: str
    theme: str
    text: str
    date_and_time: datetime


class NewsDTO(BaseModel):
    """ Новости для вывода на главной странице """

    items: list[NewsRecordDTO]
    total: int
    page: int
    size: int
    total_pages: int
