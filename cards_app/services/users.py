from cards_app.schemas.users import CurrentUserForMenuDTO
from cards_app.models.users import User


async def user_info_to_dto(user_orm: User | None) -> CurrentUserForMenuDTO | None:
    """ Преобразует данные полученные из depends в DTO
        Пока что использую во всех роутах, пока не придумаю куда деть
    """

    if user_orm:
        current_user_dto = CurrentUserForMenuDTO(id=user_orm.id,
                                              username=user_orm.username,
                                              gold=user_orm.profile.gold,
                                              diamond=user_orm.profile.diamond,
                                              )
        return current_user_dto
