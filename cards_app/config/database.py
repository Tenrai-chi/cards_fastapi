from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from .settings import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncSession:
    """ генератор сессий для подключения к бд """

    async with AsyncSessionLocal() as session:
        yield session
