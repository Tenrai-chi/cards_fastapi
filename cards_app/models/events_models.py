from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class News(Base):
    """ Новости сайта """

    __tablename__ = 'news'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    theme: Mapped[str] = mapped_column(String(200), nullable=True)
    text: Mapped[str] = mapped_column(String(2000), nullable=False)
    date_time_create: Mapped[datetime] = mapped_column(DateTime(), nullable=True)


class InitialEventAwards(Base):
    """ Награды начального события """

    __tablename__ = 'initial_event_awards'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    day_event_visit: Mapped[int] = mapped_column(Integer, nullable=True)
    type_award: Mapped[str] = mapped_column(String(30), nullable=True)
    amount_or_rarity_award: Mapped[str] = mapped_column(String(30), nullable=True)
    description: Mapped[str] = mapped_column(String(200), nullable=True)


class TeamsForBattleEvent(Base):
    """ Шаблон отряда для участия в боевом событии.
        Шаблон отряда можно изменять только вне проведения события (с 11 числа до конца месяца).
        На основе шаблона создается список участников при каждом событии.
        В одном отряде не могут быть одни и те же карты.
    """

    __tablename__ = 'teams_template_for_battle_event'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=False)
    first_card_id: Mapped[int] = mapped_column(ForeignKey('cards.id', use_alter=True), nullable=True)
    second_card_id: Mapped[int] = mapped_column(ForeignKey('cards.id', use_alter=True), nullable=True)
    third_card_id: Mapped[int] = mapped_column(ForeignKey('cards.id', use_alter=True), nullable=True)

    user = relationship('Profile', foreign_keys=[user_id], back_populates='battle_template')
    template_first_card = relationship('Card', foreign_keys=[first_card_id], back_populates='template_first_cards')
    template_second_card = relationship('Card', foreign_keys=[second_card_id], back_populates='template_second_cards')
    template_third_card = relationship('Card', foreign_keys=[third_card_id], back_populates='template_third_cards')


class BattleEventParticipants(Base):
    """ Список участников боевого события.
        При старте каждого сезона (1 числа каждого месяца) перезаписывает участников и их отряды.
        Добавляются только те участники, что сформировали полный отряд из 3 разных карт.
        Enemies -> json с противниками на каждый день. День: Противник
        Battle_progress -> json с отметками о бое на каждый день. Всего за день можно бросить вызов 1 раз. День: Участие
        Points -> полученные очки за время проведения события. За победу +100, за поражение +40.
    """

    __tablename__ = 'battle_event_participants'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=False)
    first_card_id: Mapped[int] = mapped_column(ForeignKey('cards.id', use_alter=True), nullable=True)
    second_card_id: Mapped[int] = mapped_column(ForeignKey('cards.id', use_alter=True), nullable=True)
    third_card_id: Mapped[int] = mapped_column(ForeignKey('cards.id', use_alter=True), nullable=True)
    enemies: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)
    battle_progress: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=0)

    user = relationship('Profile', foreign_keys=[user_id], back_populates='battle_participant')
    actual_first_card = relationship('Card', foreign_keys=[first_card_id], back_populates='actual_first_cards')
    actual_second_card = relationship('Card', foreign_keys=[second_card_id], back_populates='actual_second_cards')
    actual_third_card = relationship('Card', foreign_keys=[third_card_id], back_populates='actual_third_cards')


class BattleEventAwards(Base):
    """ Награды боевого события """

    __tablename__ = 'battle_event_awards'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    award: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
