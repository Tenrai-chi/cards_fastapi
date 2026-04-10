from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.config.exceptions import CardNotFoundError
from cards_app.services.events import get_total_news_count, get_paginated_news
from cards_app.schemas.news import NewsRecordDTO, NewsDTO
from cards_app.utils.common import calculate_need_exp


class ViewNewsUseCase:
    """ Use case для просмотра новостей.
        Преобразовывает новости с пагинацией
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self, page: int, size: int) -> dict:
        answer_data = {'news_dto': None,
                       'status_code': None}

        offset = (page - 1) * size
        news_models = await get_paginated_news(self.session, limit=size, offset=offset)

        total = await get_total_news_count(self.session)
        total_pages = (total + size - 1) // size

        news_records = [
            NewsRecordDTO(title=item.title,
                          theme=item.theme,
                          text=item.text,
                          date_and_time=item.date_time_create
                          )
            for item in news_models
        ]

        news_dto = NewsDTO(items=news_records,
                           total=total,
                           page=page,
                           size=size,
                           total_pages=total_pages
                           )
        answer_data['status_code'] = 200
        answer_data['news_dto'] = news_dto
        return answer_data
