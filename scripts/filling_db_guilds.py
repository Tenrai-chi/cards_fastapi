import json
import os
import sys
import logging

from pathlib import Path
from sqlalchemy import select

from cards_app.config.database import AsyncSessionLocal
from cards_app.models.guilds_models import GuildBuff

sys.path.insert(0, str(Path(__file__).parent.parent))
logger = logging.getLogger(__name__)


async def load_guild_buffs():
    """ Заполняет таблицу GuildBuff со списком усилений гильдии """

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(GuildBuff.name)
            result = await session.execute(stmt)
            existing_names = {row[0] for row in result.all()}

            file_path = os.path.join(os.path.dirname(__file__), 'db_info/guilds/guild_buffs.json')
            with open(file_path, 'r', encoding='utf-8') as file_json:
                data = json.load(file_json)
            buffs = data.get('guild_buff', [])
            new_records = []

            for buff in buffs:
                if buff['name'] not in existing_names:
                    new_records.append(GuildBuff(name=buff['name'],
                                                 description=buff['description'],
                                                 numeric_value=buff['numeric_value']
                                                 ))
                    logger.info(f'Добавлено усиление гильдии: {buff["name"]}')
                else:
                    logger.info(f'Усиление {buff["name"]} уже существует, пропускаем')

            if new_records:
                session.add_all(new_records)
                await session.commit()
                logger.info(f'Зарегистрировано {len(new_records)} усилений в guild_buff')
            else:
                logger.info('Новых усилений не добавлено')

    except FileNotFoundError as e:
        logger.error(f'Ошибка: файл не найден - {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка при разборе JSON: {e}')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка в load_guild_buffs: {e}')
