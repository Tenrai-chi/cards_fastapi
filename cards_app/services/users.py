import logging
from cards_app.schemas.users import CurrentUserForMenuDTO
from cards_app.models.users import User

logger = logging.getLogger(__name__)


async def user_info_to_dto(user_orm: User | None) -> CurrentUserForMenuDTO | None:
    """ Преобразует данные полученные из depends в DTO
        # todo Пока что использую во всех эндпоинтах, пока не придумаю куда деть
        Args:
            user_orm: Объект пользователя (User) с подгруженным профилем (Profile)
                      или None, если пользователь не авторизован.

        Returns:
            CurrentUserForMenuDTO | None: DTO для вывода информации в шапку сайта
    """

    if user_orm:
        current_user_dto = CurrentUserForMenuDTO(id=user_orm.id,
                                                 username=user_orm.username,
                                                 gold=user_orm.profile.gold,
                                                 diamond=user_orm.profile.diamond,
                                                 )
        return current_user_dto
