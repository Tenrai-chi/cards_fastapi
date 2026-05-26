import asyncio
import logging

from cards_app.config.settings import settings
from cards_app.config.logging import setup_logging

from filling_db_guilds import load_guild_buffs
from filling_db_cards import load_class_cards, load_type_cards, load_rarity_cards, load_card_store
from filling_db_events import load_battle_event_awards, load_news, load_initial_event_awards
from filling_db_exchange import (load_amulet_rarities, load_amulet_types, load_experience_items,
                                 load_upgrade_items_types, load_boxes_in_store)

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


async def safe_load(func_load, name):
    """ Функция-обертка для безопасной загрузки данных.
        Если возникает исключение, то выводит сообщение об ошибке,
        но не прерывает выполнение загрузки остальных функций.
    """

    try:
        await func_load()
    except Exception as e:
        logger.error(f'Ошибка при загрузке {name}: {e}')


async def main():
    """ Запуск всех функций для загрузки данных в бд """

    logger.info('Инициализирована загрузка данных')
    await safe_load(load_guild_buffs, 'guild_buffs')
    await safe_load(load_class_cards, 'class_cards')
    await safe_load(load_type_cards, 'types_cards')
    await safe_load(load_rarity_cards, 'rarity_cards')
    await safe_load(load_card_store, 'card_store')
    await safe_load(load_battle_event_awards, 'battle_event_awards')
    await safe_load(load_news, 'news')
    await safe_load(load_initial_event_awards, 'initial_event_awards')
    await safe_load(load_amulet_rarities, 'amulet_rarities')
    await safe_load(load_amulet_types, 'amulet_types')
    await safe_load(load_experience_items, 'experience_items')
    await safe_load(load_upgrade_items_types, 'upgrade_items_types')
    await safe_load(load_boxes_in_store, 'boxes_in_store')
    logger.info('Загрузка данных завершена!')


if __name__ == '__main__':
    asyncio.run(main())
