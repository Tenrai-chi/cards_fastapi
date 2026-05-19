from pydantic import BaseModel


class Participant(BaseModel):
    """ Участник рейтинговой битвы """

    id: int
    username: str


class FightDTO(BaseModel):
    """ Информация о прошедшей рейтинговой битве.
        Общие параметры:
            - history_fight: история битвы
            - reward_item_user: выпавшие предметы
            - reward_amulet_user: выпавшие амулеты
            - is_victory: есть ли победитель
        Если была ничья is_victory - False:
            - user: напавший пользователь
            - enemy: противник в битве
        Если победитель определен:
            - winner: победитель
            - loser: проигравший
    """

    reward_item_user: list | None = None
    reward_amulet_user: list | None = None
    history_fight: list[list] | None = None
    is_victory: bool | None = None

    winner: Participant | None = None
    loser: Participant | None = None
    user: Participant | None = None
    enemy: Participant | None = None
    error_message: str | None = None



