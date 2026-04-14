import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.auth.db_utils import store_refresh_token
from cards_app.config.security import verify_password, create_access_token, create_refresh_token, get_password_hash
from cards_app.config.settings import settings
from cards_app.models import User, Profile

logger = logging.getLogger(__name__)


async def create_user_and_profile(db_session: AsyncSession,
                                  username: str,
                                  email: str,
                                  password: str
                                  ) -> dict:
    """ Создаёт нового пользователя и связанный с ним профиль.
        Args:
            db_session: сессия базы данных
            username: имя пользователя (уникальный)
            email: email пользователя (уникальный)
            password: пароль (будет хэширован)

    Returns:
        dict:
            - user (User | None): Объект созданного пользователя или None при ошибке.
            - error_message (str | None): Текст ошибки, если она произошла, иначе None.
    """

    answer_data = {'user': None,
                   'error_message': None}
    result = await db_session.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none():
        answer_data['error_message'] = 'Пользователь с таким именем уже существует'
        logger.warning(f'Регистрация отклонена: имя пользователя "{username}" уже занято')
        return answer_data

    result = await db_session.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        logger.warning(f'Регистрация отклонена: email "{email}" уже используется')
        answer_data['error_message'] = 'Пользователь с таким email уже существует'
        return answer_data

    hashed = get_password_hash(password)
    user = User(username=username,
                email=email,
                hashed_password=hashed,
                is_active=True,
                email_verified=False)
    db_session.add(user)
    await db_session.flush()
    profile = Profile(user_id=user.id)
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(user)
    answer_data['user'] = User
    logger.info(f'Создан новый пользователь: ID {user.id} {username}')
    return answer_data


async def authenticate_and_create_tokens(db_session: AsyncSession,
                                         username: str,
                                         password: str
                                         ) -> dict:
    """ Аутентифицирует пользователя по login/email и паролю.
        При успехе обновляет поле last_login и генерирует пару success и refresh токенов
        Args:
            db_session: Асинхронная сессия SQLAlchemy.
            username: Логин или email пользователя.
            password: Пароль в открытом виде.

        Returns:
            dict:
                - user (User | None): объект пользователя при успехе
                - access_token (str | None): JWT access токен при успехе
                - refresh_token (str | None): JWT refresh токен при успехе
                - error_message (str | None): текст ошибки
    """

    answer_data = {'user': None,
                   'access_token': None,
                   'refresh_token': None,
                   'error_message': None}

    result = await db_session.execute(select(User).where((User.username == username) | (User.email == username)))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        answer_data['error_message'] = 'Неверный логин или пароль'
        logger.warning(f'Неудачная попытка входа для "{username}": неверные учётные данные')
        return answer_data
    if not user.is_active:
        answer_data['error_message'] = 'Аккаунт заблокирован, обратитесь в поддержку'
        logger.warning(f'Вход отклонён для пользователя ID {user.id} "{user.username}": аккаунт заблокирован')
        return answer_data

    user.last_login = datetime.now()
    await db_session.commit()

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    expires_at = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await store_refresh_token(db_session, user.id, refresh_token, expires_at)

    answer_data['user'] = user
    answer_data['access_token'] = access_token
    answer_data['refresh_token'] = refresh_token

    return answer_data
