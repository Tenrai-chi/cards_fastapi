from datetime import datetime
from logging import getLogger

logger = getLogger(__name__)


def time_difference_check(check_time: datetime, need_hours: int) -> tuple[bool, int]:
    """ Проверяет прошло ли необходимое количество часов для действия """

    difference = datetime.now() - check_time
    hours = int(difference.total_seconds() // 3600)

    return hours >= need_hours, hours


def calculate_need_exp(level: int) -> int:
    """ Вычисление необходимого уровня для получения следующего уровня """

    return round(1000 + 100 * 1.15 ** level)


def calculate_final_price(price: int, discount: int) -> int:
    """ Вычисление итоговой цены с учетом скидки.
        Возвращает целое число без остатка
    """

    final_price = price * (100 - discount) // 100
    return final_price

