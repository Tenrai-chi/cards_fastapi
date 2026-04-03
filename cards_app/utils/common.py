from datetime import datetime
from random import choice, randint
from logging import getLogger

logger = getLogger(__name__)


def time_difference_check(check_time: datetime, need_hours: int) -> tuple[bool, float]:
    """ Проверяет прошло ли необходимое количество часов для действия """

    difference = datetime.now() - check_time
    hours = difference.total_seconds() // 3600

    return hours >= need_hours, hours


def calculate_need_exp(level: int) -> int:
    """ Вычисление необходимого уровня для получения следующего уровня """

    return round(1000 + 100 * 1.15 ** level)

