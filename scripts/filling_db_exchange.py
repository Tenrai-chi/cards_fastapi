import json
import os
import sys
import logging

from pathlib import Path
from sqlalchemy import select

from cards_app.config.database import AsyncSessionLocal
from cards_app.config.settings import settings
from cards_app.models.exchange import AmuletRarity, AmuletType, ExperienceItems, UpgradeItemsType, Boxes

sys.path.insert(0, str(Path(__file__).parent.parent))
logger = logging.getLogger(__name__)


async def load_amulet_rarities():
    """ Заполняет таблицу AmuletRarity со списком редкости амулетов """

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(AmuletRarity.name)
            result = await session.execute(stmt)
            existing_names = {row[0] for row in result.all()}

            file_path = os.path.join(os.path.dirname(__file__), 'db_info/exchange/amulet_rarities.json')
            with open(file_path, 'r', encoding='utf-8') as file_json:
                data = json.load(file_json)
            all_rarities = data.get('amulet_rarity', [])
            new_records = []

            for rarity in all_rarities:
                if rarity['name'] not in existing_names:
                    new_records.append(AmuletRarity(name=rarity['name'],
                                                    chance_drop_on_fight=rarity['chance_drop_on_fight'],
                                                    chance_drop_on_box=rarity['chance_drop_on_box'],
                                                    max_upgrade=rarity['max_upgrade'],
                                                    ))
                    logger.info(f'Добавлена редкость амулетов: {rarity["name"]}')
                else:
                    logger.info(f'Редкость амулетов {rarity["name"]} уже существует, пропускаем')

            if new_records:
                session.add_all(new_records)
                await session.commit()
                logger.info(f'Зарегистрировано {len(new_records)} редкостей амулетов')
            else:
                logger.info('Новых редкостей амулетов не добавлено')

    except FileNotFoundError as e:
        logger.error(f'Ошибка: файл не найден - {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка при разборе JSON: {e}')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка в load_amulet_rarities: {e}')


async def load_amulet_types():
    """ Заполняет таблицу AmuletType со списком типов амулетов """

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(AmuletType.name)
            result = await session.execute(stmt)
            existing_names = {row[0] for row in result.all()}

            file_path = os.path.join(os.path.dirname(__file__), 'db_info/exchange/amulet_types.json')
            with open(file_path, 'r', encoding='utf-8') as file_json:
                data = json.load(file_json)
            all_types= data.get('amulet_type', [])
            new_records = []

            rarity_result = await session.execute(select(AmuletRarity))
            rarity_map = {rarity.name: rarity for rarity in rarity_result.scalars().all()}

            for amulet_type in all_types:
                image_path = amulet_type['image']
                full_image_path = settings.STATIC_DIR / image_path

                if not full_image_path.exists():
                    logger.error(f'Предупреждение: файл {full_image_path} не найден для типа амулета {amulet_type["name"]}')
                    continue

                if amulet_type['name'] not in existing_names:
                    rarity_name = amulet_type['rarity']
                    rarity_obj = rarity_map.get(rarity_name)
                    new_records.append(AmuletType(name=amulet_type['name'],
                                                  bonus_hp=amulet_type['bonus_hp'],
                                                  bonus_damage=amulet_type['bonus_damage'],
                                                  price=amulet_type['price'],
                                                  sale_now=amulet_type['sale_now'],
                                                  image=amulet_type['image'],
                                                  discount=amulet_type['discount'],
                                                  discount_now=amulet_type['discount_now'],
                                                  rarity_id=rarity_obj.id,
                                                  ))
                    logger.info(f'Добавлен тип амулета: {amulet_type["name"]}')
                else:
                    logger.info(f'Тип амулета {amulet_type["name"]} уже существует, пропускаем')

            if new_records:
                session.add_all(new_records)
                await session.commit()
                logger.info(f'Зарегистрировано {len(new_records)} типов амулетов')
            else:
                logger.info('Новых типов амулетов не добавлено')

    except FileNotFoundError as e:
        logger.error(f'Ошибка: файл не найден - {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка при разборе JSON: {e}')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка в load_amulet_types: {e}')


async def load_experience_items():
    """ Заполняет таблицу ExperienceItems со списком книг опыта """

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(ExperienceItems.name)
            result = await session.execute(stmt)
            existing_names = {row[0] for row in result.all()}

            file_path = os.path.join(os.path.dirname(__file__), 'db_info/exchange/experience_items.json')
            with open(file_path, 'r', encoding='utf-8') as file_json:
                data = json.load(file_json)
            all_items = data.get('experience_items', [])
            new_records = []

            for item in all_items:
                image_path = item['image']
                full_image_path = settings.STATIC_DIR / image_path

                if not full_image_path.exists():
                    logger.error(f'Предупреждение: файл {full_image_path} не найден для {item["name"]}')
                    continue

                if item['name'] not in existing_names:
                    new_records.append(ExperienceItems(name=item['name'],
                                                       rarity=item['rarity'],
                                                       experience_amount=item['experience_amount'],
                                                       chance_drop_on_fight=item['chance_drop_on_fight'],
                                                       chance_drop_on_box=item['chance_drop_on_box'],
                                                       price=item['price'],
                                                       image=item['image'],
                                                       gold_for_use=item['gold_for_use'],
                                                       sale_now=bool(item['sale_now']),
                                                       ))
                    logger.info(f'Добавлена: {item["name"]}')
                else:
                    logger.info(f'{item["name"]} уже существует, пропускаем')

            if new_records:
                session.add_all(new_records)
                await session.commit()
                logger.info(f'Зарегистрировано {len(new_records)} книг опыта')
            else:
                logger.info('Новых книг опыта не зарегистрировано')

    except FileNotFoundError as e:
        logger.error(f'Ошибка: файл не найден - {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка при разборе JSON: {e}')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка в load_experience_items: {e}')


async def load_upgrade_items_types():
    """ Заполняет таблицу UpgradeItemsType со списком предметов усилений """

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(UpgradeItemsType.name)
            result = await session.execute(stmt)
            existing_names = {row[0] for row in result.all()}

            file_path = os.path.join(os.path.dirname(__file__), 'db_info/exchange/upgrade_items_types.json')
            with open(file_path, 'r', encoding='utf-8') as file_json:
                data = json.load(file_json)
            all_items = data.get('upgrade_items_type', [])
            new_records = []

            for item_type in all_items:
                image_path = item_type['image']
                full_image_path = settings.STATIC_DIR / image_path

                if not full_image_path.exists():
                    logger.error(f'Предупреждение: файл {full_image_path} не найден для {item_type["name"]}')
                    continue

                if item_type['name'] not in existing_names:
                    new_records.append(UpgradeItemsType(name=item_type['name'],
                                                        description=item_type['description'],
                                                        type=item_type['type'],
                                                        amount_up=item_type['amount_up'],
                                                        image=item_type['image'],
                                                        price=item_type['price'],
                                                        price_of_use=item_type['price_of_use'],
                                                       ))
                    logger.info(f'Добавлен тип предмета усиления: {item_type["name"]}')
                else:
                    logger.info(f'Тип предмета усиления {item_type["name"]} уже существует, пропускаем')

            if new_records:
                session.add_all(new_records)
                await session.commit()
                logger.info(f'Зарегистрировано {len(new_records)} предметов усилений')
            else:
                logger.info('Новых предметов усилений не зарегистрировано')

    except FileNotFoundError as e:
        logger.error(f'Ошибка: файл не найден - {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка при разборе JSON: {e}')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка в load_upgrade_items_types: {e}')


async def load_boxes_in_store():
    """ Заполняет таблицу Boxes со списком предметов усилений """

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Boxes.name)
            result = await session.execute(stmt)
            existing_names = {row[0] for row in result.all()}

            file_path = os.path.join(os.path.dirname(__file__), 'db_info/store/item_store.json')
            with open(file_path, 'r', encoding='utf-8') as file_json:
                data = json.load(file_json)
            all_boxes = data.get('box_store', [])
            new_records = []

            for box in all_boxes:
                image_path = box['image']
                full_image_path = settings.STATIC_DIR / image_path

                if not full_image_path.exists():
                    logger.error(f'Предупреждение: файл {full_image_path} не найден для {box["name"]}')
                    continue

                if box['name'] not in existing_names:
                    new_records.append(Boxes(name=box['name'],
                                             description=box['description'],
                                             image=box['image'],
                                             price=box['price'],
                                             reward_type=box['reward_type'],
                                             reward_amount=box['reward_amount']
                                             ))
                    logger.info(f'Добавлен сундук в магазин: {box["name"]}')
                else:
                    logger.info(f'Сундук {box["name"]} уже существует в магазине, пропускаем')

            if new_records:
                session.add_all(new_records)
                await session.commit()
                logger.info(f'Зарегистрировано {len(new_records)} сундуков в магазине')
            else:
                logger.info('Новых сундуков в магазине не зарегистрировано')

    except FileNotFoundError as e:
        logger.error(f'Ошибка: файл не найден - {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка при разборе JSON: {e}')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка в load_boxes_in_store: {e}')
