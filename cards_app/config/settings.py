import os

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from dotenv import load_dotenv


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent
    load_dotenv()

    STATIC_DIR: Path = BASE_DIR / 'static'
    MEDIA_DIR: Path = BASE_DIR / 'media'

    STATIC_URL: str = '/static'
    MEDIA_URL: str = '/media'

    DB_NAME: str = os.getenv('DB_NAME')
    DB_USER: str = os.getenv('DB_USER')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD')
    DB_HOST: str = os.getenv('DB_HOST')
    DB_PORT: str = os.getenv('DB_PORT')

    SECRET_KEY: str = os.getenv('SECRET_KEY')

    REDIS_HOST: str = os.getenv('REDIS_HOST')
    REDIS_PORT: str = os.getenv('REDIS_PORT')
    REDIS_DB: str = os.getenv('REDIS_DB')
    REDIS_URL: str = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

    LOG_LEVEL: str = 'INFO'

    SECRET_KEY_FOR_HASH: str = os.getenv('SECRET_KEY_FOR_HASH')
    ALGORITHM: str = os.getenv('ALGORITHM')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')
    REFRESH_TOKEN_EXPIRE_DAYS: int = os.getenv('REFRESH_TOKEN_EXPIRE_DAYS')

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    model_config = SettingsConfigDict(env_file=str(Path(__file__).parent.parent.parent / '.env'),
                                      env_file_encoding='utf-8',
                                      )


settings = Settings()
