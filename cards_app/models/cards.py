from datetime import datetime

from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ClassCard(Base):
    """ Модель класса карты.
        Отвечает за отображение карты и ее способность, в т.ч в истории боя
    """

    __tablename__ = 'class_cards'
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    skill: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    description_for_history_fight: Mapped[str] = mapped_column(String(500), nullable=False)
    numeric_value: Mapped[float] = mapped_column(Float, nullable=True)
    chance_use: Mapped[int] = mapped_column(Integer, nullable=False)
    image: Mapped[str] = mapped_column(String(255), nullable=False)

    cards = relationship('Card', foreign_keys='[Card.class_card_id]', back_populates='class_card')
    store_cards = relationship('CardStore', foreign_keys='[CardStore.class_card_id]', back_populates='class_card')


class Type(Base):
    """ Модель типа карты.
        Отвечает за урон карты по цветовой схеме
    """

    __tablename__ = 'type_cards'
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(10), nullable=False)
    better_id: Mapped[int] = mapped_column(ForeignKey('type_cards.id', use_alter=True), nullable=True)
    worst_id: Mapped[int] = mapped_column(ForeignKey('type_cards.id', use_alter=True), nullable=True)

    better = relationship('Type', foreign_keys=[better_id], remote_side=[id])
    worst = relationship('Type', foreign_keys=[worst_id], remote_side=[id])
    cards = relationship('Card', foreign_keys='[Card.type_id]', back_populates='type_card')
    store_cards = relationship('CardStore', foreign_keys='[CardStore.type_id]', back_populates='type_card')


class Rarity(Base):
    """ Модель редкости карты.
        Отвечает за максимально возможный уровень, разброс здоровья и урона при генерации карты
        и увеличение характеристик с ростом уровня
    """

    __tablename__ = 'rarity_cards'
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(2), nullable=False)
    max_level: Mapped[int] = mapped_column(Integer, nullable=False)
    coefficient_damage_for_level: Mapped[float] = mapped_column(Float, nullable=False)
    coefficient_hp_for_level: Mapped[float] = mapped_column(Float, nullable=False)
    min_hp: Mapped[int] = mapped_column(Integer, nullable=False)
    max_hp: Mapped[int] = mapped_column(Integer, nullable=False)
    min_damage: Mapped[int] = mapped_column(Integer, nullable=False)
    max_damage: Mapped[int] = mapped_column(Integer, nullable=False)
    drop_chance: Mapped[int] = mapped_column(Integer, nullable=False)

    cards = relationship('Card', foreign_keys='[Card.rarity_id]', back_populates='rarity_card')
    store_cards = relationship('CardStore', foreign_keys='[CardStore.rarity_id]', back_populates='rarity_card')


class Card(Base):
    """ Модель карт пользователей.
        Class -> способности карты в бою и картинка
        Type -> цвет карты (зеленый, синий, красный) по принципу камень-ножницы-бумага
        Rarity -> максимальный уровень, разброс характеристик начального уровня при генерации, увеличение характеристик с уровнем
        Damage -> базовый урон
        Hp -> базовое здоровье
        Enhancement -> количество использований увеличения здоровья и урона
        Merger -> количество использованных копий карты, усиливает на навык карты в бою (изначально 0)
    """

    __tablename__ = 'cards'
    id: Mapped[int] = mapped_column(primary_key=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=True, index=True)
    class_card_id: Mapped[int] = mapped_column(ForeignKey('class_cards.id'), nullable=False)
    type_id: Mapped[int] = mapped_column(ForeignKey('type_cards.id'), nullable=False)
    rarity_id: Mapped[int] = mapped_column(ForeignKey('rarity_cards.id'), nullable=False)
    hp: Mapped[float] = mapped_column(Float, nullable=False)
    damage: Mapped[float] = mapped_column(Float, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1)
    experience_bar: Mapped[int] = mapped_column(Integer, default=0)
    sale_status: Mapped[bool] = mapped_column(Boolean, default=False)
    price: Mapped[int] = mapped_column(Integer, nullable=True)
    enhancement: Mapped[int] = mapped_column(Integer, default=0)
    max_enhancement: Mapped[int] = mapped_column(Integer, default=20)
    merger: Mapped[int] = mapped_column(Integer, default=0)
    max_merger: Mapped[int] = mapped_column(Integer, default=10)

    class_card = relationship('ClassCard', foreign_keys=[class_card_id], back_populates='cards')
    type_card = relationship('Type', foreign_keys=[type_id],  back_populates='cards')
    rarity_card = relationship('Rarity', foreign_keys=[rarity_id], back_populates='cards')
    owner = relationship('Profile', foreign_keys='[Card.owner_id]', back_populates='cards')
    selected_by = relationship('Profile', foreign_keys='[Profile.current_card_id]', back_populates='current_card')
    won_fights = relationship('FightHistory', foreign_keys='[FightHistory.card_winner_id]',
                              back_populates='card_winner')
    lost_fights = relationship('FightHistory', foreign_keys='[FightHistory.card_loser_id]',
                               back_populates='card_loser')
    receiving_history = relationship('HistoryReceivingCards', foreign_keys='[HistoryReceivingCards.card_id]', back_populates='card')
    sale_records = relationship('SaleUserCards', foreign_keys='[SaleUserCards.card_id]',  back_populates='card')
    amulet = relationship('AmuletItem', foreign_keys='[AmuletItem.card_id]',  back_populates='card', uselist=False)

    template_first_cards = relationship('TeamsForBattleEvent',
                                        foreign_keys='[TeamsForBattleEvent.first_card_id]',
                                        back_populates='template_first_card')
    template_second_cards = relationship('TeamsForBattleEvent',
                                         foreign_keys='[TeamsForBattleEvent.second_card_id]',
                                         back_populates='template_second_card')
    template_third_cards = relationship('TeamsForBattleEvent',
                                        foreign_keys='[TeamsForBattleEvent.third_card_id]',
                                        back_populates='template_third_card')

    actual_first_cards = relationship('BattleEventParticipants',
                                      foreign_keys='[BattleEventParticipants.first_card_id]',
                                      back_populates='actual_first_card')
    actual_second_cards = relationship('BattleEventParticipants',
                                       foreign_keys='[BattleEventParticipants.second_card_id]',
                                       back_populates='actual_second_card')
    actual_third_cards = relationship('BattleEventParticipants',
                                      foreign_keys='[BattleEventParticipants.third_card_id]',
                                      back_populates='actual_third_card')


class CardStore(Base):
    """ Модель карт в магазине карт.
        При покупке карты используется как шаблон создания карты пользователя.
    """

    __tablename__ = 'card_store'
    id: Mapped[int] = mapped_column(primary_key=True)

    class_card_id: Mapped[int] = mapped_column(ForeignKey('class_cards.id'), nullable=False)
    type_id: Mapped[int] = mapped_column(ForeignKey('type_cards.id'), nullable=False)
    rarity_id: Mapped[int] = mapped_column(ForeignKey('rarity_cards.id'), nullable=False)
    hp: Mapped[int] = mapped_column(Integer, nullable=False)
    damage: Mapped[int] = mapped_column(Integer, nullable=False)
    sale_now: Mapped[bool] = mapped_column(Boolean, default=False)
    price: Mapped[int] = mapped_column(Integer, default=0)
    discount: Mapped[int] = mapped_column(Integer, default=0)
    discount_now: Mapped[bool] = mapped_column(Boolean, default=False)

    class_card = relationship('ClassCard', foreign_keys=[class_card_id], back_populates='store_cards')
    type_card = relationship('Type', foreign_keys=[type_id],  back_populates='store_cards')
    rarity_card = relationship('Rarity', foreign_keys=[rarity_id],  back_populates='store_cards')


class HistoryReceivingCards(Base):
    """ Модель истории получения карт.
        Описывает момент создания карты, будь это покупка или бесплатное получение
    """

    __tablename__ = 'history_receiving_cards'
    id: Mapped[int] = mapped_column(primary_key=True)

    card_id: Mapped[int] = mapped_column(ForeignKey('cards.id'), nullable=False)
    date_and_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=False)
    method_receiving: Mapped[str] = mapped_column(String(20), nullable=True)

    card = relationship('Card', foreign_keys=[card_id], back_populates='receiving_history')
    user = relationship('Profile', foreign_keys=[user_id], back_populates='cards_received')
