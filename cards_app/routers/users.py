from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from cards_app.auth.dependencies import get_current_user_with_profile
from cards_app.models import User
from cards_app.config.database import get_db_session
from cards_app.config.settings import settings
from cards_app.use_cases.profile import ViewProfileUseCase
from cards_app.config.exceptions import *
from cards_app.services.users import user_info_to_dto

router = APIRouter(prefix='/users', tags=['users'])

templates = Jinja2Templates(directory=str(settings.BASE_DIR / 'templates'))


@router.get('/{user_id}')
async def view_user_profile(request: Request,
                            user_id: int,
                            session_db: AsyncSession = Depends(get_db_session),
                            current_user: User | None = Depends(get_current_user_with_profile),
                            ):
    """ Просмотр профиля пользователя """

    use_case = ViewProfileUseCase(session_db)
    current_user_dto = await user_info_to_dto(current_user)
    try:
        profile_dto = await use_case.execute(current_user, user_id)
    except UserNotFoundError:
        return templates.TemplateResponse(
            request=request,
            name='error_page.html',
            context={'error': 'Пользователь не найден', 'error_code': 404},
            status_code=404
        )

    except Exception as error:
        print(f'ОШИБКА АААААА {error}')
        # Случайная ошибка доделать
        return templates.TemplateResponse(
            request=request,
            name='error_page.html',
            context={'error': 'Внутренняя ошибка сервера', 'error_code': 500},
            status_code=500
        )

    context = {
        'request': request,
        'current_user': current_user_dto,
        'profile_dto': profile_dto,
    }
    return templates.TemplateResponse(request, 'profile.html', context)
