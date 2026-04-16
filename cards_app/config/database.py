import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from .settings import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

logger = logging.getLogger(__name__)


async def get_db_session() -> AsyncSession:
    """ Генератор сессий для подключения к бд """

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except SQLAlchemyError as error:
            await session.rollback()
            logger.error(f'Ошибка при работе сессии sql: {error}')
            raise
