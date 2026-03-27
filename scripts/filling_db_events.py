import json
import os
import sys
import logging

from datetime import datetime
from pathlib import Path
from sqlalchemy import select

from cards_app.config.database import AsyncSessionLocal
from cards_app.models.events_models import News, BattleEventAwards, InitialEventAwards

sys.path.insert(0, str(Path(__file__).parent.parent))
logger = logging.getLogger(__name__)


async def load_battle_event_awards():
    """ Заполняет таблицу BattleEventAwards со списком наград боевого события """

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(BattleEventAwards.rank)
            result = await session.execute(stmt)
            existing_ranks = {row[0] for row in result.all()}

            file_path = os.path.join(os.path.dirname(__file__), 'db_info/events/battle_event_awards.json')
            with open(file_path, 'r', encoding='utf-8') as file_json:
                data = json.load(file_json)
            all_awards = data.get('event_awards', [])
            new_records = []

            for award in all_awards:
                if award['rank'] not in existing_ranks:
                    new_records.append(BattleEventAwards(rank=award['rank'],
                                                         award=award['award'],
                                                         amount=award['amount'],
                                                         ))
                    logger.info(f'Добавлена награда ранга {award["rank"]} в боевом событии')
                else:
                    logger.info(f'Награда ранга {award["rank"]} уже существует, пропускаем')

            if new_records:
                session.add_all(new_records)
                await session.commit()
                logger.info(f'Зарегистрировано {len(new_records)} наград в боевом событии')
            else:
                logger.info('Новых наград боевого события не добавлено')

    except FileNotFoundError as e:
        logger.error(f'Ошибка: файл не найден - {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка при разборе JSON: {e}')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка в load_battle_event_awards: {e}')


async def load_news():
    """ Заполняет таблицу News с новостями сайта """

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(News.title)
            result = await session.execute(stmt)
            existing_news = {row[0] for row in result.all()}

            file_path = os.path.join(os.path.dirname(__file__), 'db_info/events/news.json')
            with open(file_path, 'r', encoding='utf-8') as file_json:
                data = json.load(file_json)
            all_news = data.get('news', [])
            new_records = []

            for new in all_news:
                if new['title'] not in existing_news:
                    date_str = new['date_time_create']
                    dt = datetime.fromisoformat(date_str)
                    new_records.append(News(title=new['title'],
                                            theme=new['theme'],
                                            text=new['text'],
                                            date_time_create=dt,
                                            ))
                    logger.info(f'Добавлена новость {new["title"]}')
                else:
                    logger.info(f'Новость {new["title"]} уже существует, пропускаем')

            if new_records:
                session.add_all(new_records)
                await session.commit()
                logger.info(f'Зарегистрировано {len(new_records)} новостей')
            else:
                logger.info('Новых новостей')

    except FileNotFoundError as e:
        logger.error(f'Ошибка: файл не найден - {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка при разборе JSON: {e}')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка в load_news: {e}')


async def load_initial_event_awards():
    """ Заполняет таблицу InitialEventAwards со списком наград стартового события """

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(InitialEventAwards.day_event_visit)
            result = await session.execute(stmt)
            existing_ranks = {row[0] for row in result.all()}

            file_path = os.path.join(os.path.dirname(__file__), 'db_info/events/initial_event_awards.json')
            with open(file_path, 'r', encoding='utf-8') as file_json:
                data = json.load(file_json)
            all_awards = data.get('event_awards', [])
            new_records = []

            for award in all_awards:
                if award['day_event_visit'] not in existing_ranks:
                    new_records.append(InitialEventAwards(day_event_visit=award['day_event_visit'],
                                                          type_award=award['type_award'],
                                                          amount_or_rarity_award=award['amount_or_rarity_award'],
                                                          description=award['description'],
                                                          ))
                    logger.info(f'Добавлена награда дня {award["day_event_visit"]} в стартовом событии')
                else:
                    logger.info(f'Награда дня {award["day_event_visit"]} уже существует, пропускаем')

            if new_records:
                session.add_all(new_records)
                await session.commit()
                logger.info(f'Зарегистрировано {len(new_records)} наград в стартовом событии')
            else:
                logger.info('Новых наград стартового события не добавлено')

    except FileNotFoundError as e:
        logger.error(f'Ошибка: файл не найден - {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка при разборе JSON: {e}')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка в load_initial_event_awards: {e}')
