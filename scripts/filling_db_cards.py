import json
import os
import sys
import logging

from pathlib import Path
from sqlalchemy import select
from cards_app.config.settings import settings

from cards_app.config.database import AsyncSessionLocal
from cards_app.models.cards import ClassCard, Type, Rarity, CardStore

sys.path.insert(0, str(Path(__file__).parent.parent))
logger = logging.getLogger(__name__)


async def load_class_cards():
    """ Заполняет таблицу ClassCard со списком классов карт """

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(ClassCard.name)
            result = await session.execute(stmt)
            existing_names = {row[0] for row in result.all()}

            file_path = os.path.join(os.path.dirname(__file__), 'db_info/cards/class_cards.json')
            with open(file_path, 'r', encoding='utf-8') as file_json:
                data = json.load(file_json)
            all_classes = data.get('class_card', [])
            new_records = []

            for class_card in all_classes:
                image_path = class_card['image']
                full_image_path = settings.STATIC_DIR / image_path

                if not full_image_path.exists():
                    logger.error(f'Предупреждение: файл {full_image_path} не найден для класса {class_card["name"]}')
                    continue

                if class_card['name'] not in existing_names:
                    new_records.append(
                        ClassCard(
                            name=class_card['name'],
                            skill=class_card['skill'],
                            description=class_card['description'],
                            description_for_history_fight=class_card['description_for_history_fight'],
                            numeric_value=class_card['numeric_value'],
                            chance_use=class_card['chance_use'],
                            image=class_card['image'],
                        )
                    )
                    logger.info(f'Добавлен класс карт: {class_card["name"]}')
                else:
                    logger.info(f'Класс карт {class_card["name"]} уже существует, пропускаем')

            if new_records:
                session.add_all(new_records)
                await session.commit()
                logger.info(f'Зарегистрировано {len(new_records)} классов карт')
            else:
                logger.info('Новых классов карт не добавлено')

    except FileNotFoundError as e:
        logger.error(f'Ошибка: файл не найден - {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка при разборе JSON: {e}')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка в load_class_cards: {e}')


async def load_type_cards():
    """
    Заполняет таблицу Type со списком типов карт,
    а затем отдельной транзакцией устанавливает связи.
    """

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Type.name)
            result = await session.execute(stmt)
            existing_names = {row[0] for row in result.all()}

            file_path = os.path.join(os.path.dirname(__file__), 'db_info/cards/type_cards.json')
            with open(file_path, 'r', encoding='utf-8') as file_json:
                data = json.load(file_json)
            all_types = data.get('type', [])
            new_records = []

            for type_card in all_types:
                if type_card['name'] not in existing_names:
                    new_records.append(Type(name=type_card['name']))
                    logger.info(f'Добавлен тип карт: {type_card["name"]}')
                else:
                    logger.info(f'Тип карт {type_card["name"]} уже существует, пропускаем')

            if new_records:
                session.add_all(new_records)
                await session.commit()
                logger.info(f'Зарегистрировано {len(new_records)} типов карт')
            else:
                logger.info('Новых типов карт не добавлено')

            stmt = select(Type).where(Type.name.in_(['Красный', 'Зеленый', 'Синий']))
            result = await session.execute(stmt)
            types = {t.name: t for t in result.scalars().all()}
            if len(types) != 3:
                logger.error('Не найдены все три типа, связи не устанавливаются')
                return

            green_type = types['Зеленый']
            red_type = types['Красный']
            blue_type = types['Синий']

            if all(
                    [
                        green_type.better_id is not None, green_type.worst_id is not None,
                        red_type.better_id is not None, red_type.worst_id is not None,
                        blue_type.better_id is not None, blue_type.worst_id is not None
                    ]
            ):
                logger.info('Связи между типами уже существуют, пропускаем')

            else:
                green_type.better_id = blue_type.id
                green_type.worst_id = red_type.id

                red_type.better_id = green_type.id
                red_type.worst_id = blue_type.id

                blue_type.better_id = red_type.id
                blue_type.worst_id = green_type.id

                await session.commit()
                logger.info('Связи между типами установлены')

    except FileNotFoundError as e:
        logger.error(f'Ошибка: файл не найден - {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка при разборе JSON: {e}')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка в load_type_cards: {e}')


async def load_rarity_cards():
    """ Заполняет таблицу Rarity со списком редкостей карт """

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Rarity.name)
            result = await session.execute(stmt)
            existing_names = {row[0] for row in result.all()}

            file_path = os.path.join(os.path.dirname(__file__), 'db_info/cards/rarity_cards.json')
            with open(file_path, 'r', encoding='utf-8') as file_json:
                data = json.load(file_json)
            all_rarities = data.get('rarity', [])
            new_records = []

            for rarity in all_rarities:
                if rarity['name'] not in existing_names:
                    new_records.append(Rarity(
                        name=rarity['name'],
                        max_level=rarity['max_level'],
                        coefficient_damage_for_level=rarity['coefficient_damage_for_level'],
                        coefficient_hp_for_level=rarity['coefficient_hp_for_level'],
                        min_hp=rarity['min_hp'],
                        max_hp=rarity['max_hp'],
                        min_damage=rarity['min_damage'],
                        max_damage=rarity['max_damage'],
                        drop_chance=rarity['drop_chance'],
                    )
                    )
                    logger.info(f'Добавлена редкость карт: {rarity["name"]}')
                else:
                    logger.info(f'Редкость карт {rarity["name"]} уже существует, пропускаем')

            if new_records:
                session.add_all(new_records)
                await session.commit()
                logger.info(f'Зарегистрировано {len(new_records)} редкостей карт')
            else:
                logger.info('Новых редкостей карт не добавлено')

    except FileNotFoundError as e:
        logger.error(f'Ошибка: файл не найден - {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка при разборе JSON: {e}')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка в load_rarity_cards: {e}')


async def load_card_store():
    """
    Заполняет таблицу CardStore со списком карт в магазине.
    Проверяет наличие карты в бд по классу, редкости и типу.
    """

    try:
        async with AsyncSessionLocal() as session:
            file_path = os.path.join(os.path.dirname(__file__), 'db_info/cards/card_store.json')
            with open(file_path, 'r', encoding='utf-8') as file_json:
                data = json.load(file_json)
            all_cards = data.get('card_store', [])

            # Все карты в магазине
            existing_stmt = select(CardStore)
            existing_result = await session.execute(existing_stmt)
            existing_cards = {
                (card.class_card_id, card.type_id, card.rarity_id): card
                for card in existing_result.scalars().all()
            }

            # Все классы, типы и редкости в словарях
            class_result = await session.execute(select(ClassCard))
            class_map = {c.name: c for c in class_result.scalars().all()}

            type_result = await session.execute(select(Type))
            type_map = {t.name: t for t in type_result.scalars().all()}

            rarity_result = await session.execute(select(Rarity))
            rarity_map = {r.name: r for r in rarity_result.scalars().all()}

            new_records = []
            for card in all_cards:
                class_name = card.get('class_card')
                type_name = card.get('type')
                rarity_name = card.get('rarity')

                class_obj = class_map.get(class_name)
                type_obj = type_map.get(type_name)
                rarity_obj = rarity_map.get(rarity_name)

                key = (class_obj.id, type_obj.id, rarity_obj.id)
                if key in existing_cards:
                    logger.info(f'Карта {class_name} / {type_name} / {rarity_name} уже существует, пропускаем')
                    continue

                new_records.append(CardStore(
                    class_card_id=class_obj.id,
                    type_id=type_obj.id,
                    rarity_id=rarity_obj.id,
                    hp=card['hp'],
                    damage=card['damage'],
                    sale_now=bool(card['sale_now']),
                    price=card['price'],
                    discount=card['discount'],
                    discount_now=bool(card['discount_now']),
                )
                )
                logger.info(f'Добавлена карта в магазин: {class_name} / {type_name} / {rarity_name}')

            if new_records:
                session.add_all(new_records)
                await session.commit()
                logger.info(f'Зарегистрировано {len(new_records)} карт в магазине')
            else:
                logger.info('Новых карт в магазине не добавлено')

    except FileNotFoundError as e:
        logger.error(f'Ошибка: файл не найден - {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Ошибка при разборе JSON: {e}')
    except Exception as e:
        logger.error(f'Произошла непредвиденная ошибка в load_card_store: {e}')
