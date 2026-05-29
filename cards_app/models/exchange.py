from datetime import datetime

from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Float, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class SaleUserCards(Base):
    """ Модель с историей покупок карт между пользователями """

    __tablename__ = 'sale_user_cards'
    id: Mapped[int] = mapped_column(primary_key=True)

    date_and_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=True)
    salesman_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=True)
    card_id: Mapped[int] = mapped_column(ForeignKey('cards.id'), nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=True)
    transaction_buyer_id: Mapped[int] = mapped_column(ForeignKey('transactions.id'), nullable=True)
    transaction_salesman_id: Mapped[int] = mapped_column(ForeignKey('transactions.id'), nullable=True)

    buyer = relationship('Profile', foreign_keys=[buyer_id], back_populates='purchases')
    salesman = relationship('Profile', foreign_keys=[salesman_id], back_populates='sales')
    card = relationship('Card', foreign_keys=[card_id], back_populates='sale_records')
    transaction_buyer = relationship('Transactions', foreign_keys=[transaction_buyer_id],
                                     back_populates='buyer_transactions')
    transaction_salesman = relationship('Transactions', foreign_keys=[transaction_salesman_id],
                                        back_populates='seller_transactions')


class ExperienceItems(Base):
    """ Модель с существующими типами предметов опыта.
        Используется для повышения уровня карты.
        Не изменяется системой, загружается через заполнение модели
    """

    __tablename__ = 'experience_items'
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(50), nullable=True)
    rarity: Mapped[str] = mapped_column(String(3), nullable=True)
    experience_amount: Mapped[int] = mapped_column(Integer, nullable=True)
    chance_drop_on_fight: Mapped[int] = mapped_column(Integer, nullable=True)
    chance_drop_on_box: Mapped[int] = mapped_column(Integer, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=True)
    image: Mapped[str] = mapped_column(String(255), nullable=True)
    gold_for_use: Mapped[int] = mapped_column(Integer, nullable=True)
    sale_now: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)

    inventory_items = relationship('UsersInventory', foreign_keys='[UsersInventory.item_id]', back_populates='item')
    purchase_history = relationship('HistoryPurchaseItems', foreign_keys='[HistoryPurchaseItems.item_id]',  back_populates='item')


class UsersInventory(Base):
    """ Модель, описывающая наличие предметов опыта всех пользователей """

    __tablename__ = 'users_inventory'
    id: Mapped[int] = mapped_column(primary_key=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('experience_items.id'), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)

    owner = relationship('Profile', foreign_keys=[owner_id], back_populates='inventory')
    item = relationship('ExperienceItems', foreign_keys=[item_id],  back_populates='inventory_items')

    __table_args__ = (
        CheckConstraint('amount >= 0', name='check_amount'),
    )


class HistoryPurchaseItems(Base):
    """ Модель с историей покупок в магазине """

    __tablename__ = 'history_purchase_items'
    id: Mapped[int] = mapped_column(primary_key=True)

    date_and_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('experience_items.id'), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey('transactions.id'), nullable=True)

    user = relationship('Profile', foreign_keys=[user_id],  back_populates='purchased_items')
    item = relationship('ExperienceItems', foreign_keys=[item_id],  back_populates='purchase_history')
    transaction = relationship('Transactions', foreign_keys=[transaction_id],  back_populates='item_purchases')


class AmuletRarity(Base):
    """ Модель с редкостью амулетов.
        Используется для расчета шанса выпадения при битвах и усилениях амулетов.
        Не изменяется системой, загружается через заполнение модели
    """

    __tablename__ = 'amulet_rarities'
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(30), nullable=False)
    chance_drop_on_fight: Mapped[int] = mapped_column(Integer, nullable=True)
    chance_drop_on_box: Mapped[int] = mapped_column(Integer, nullable=True)
    max_upgrade: Mapped[int] = mapped_column(Integer, nullable=True)

    amulet_types = relationship('AmuletType', foreign_keys='[AmuletType.rarity_id]', back_populates='rarity')


class AmuletType(Base):
    """ Модель со всеми существующими типами амулетов.
        Не изменяется системой, загружается через заполнение модели
    """

    __tablename__ = 'amulet_types'
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(30), nullable=False)
    bonus_hp: Mapped[float] = mapped_column(Float, nullable=True)
    bonus_damage: Mapped[float] = mapped_column(Float, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=True)
    sale_now: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)
    image: Mapped[str] = mapped_column(String(255), nullable=True)
    discount: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    discount_now: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    rarity_id: Mapped[int] = mapped_column(ForeignKey('amulet_rarities.id'), nullable=True)

    rarity = relationship('AmuletRarity', foreign_keys=[rarity_id],  back_populates='amulet_types')
    amulets_in_inventory = relationship('AmuletItem', foreign_keys='[AmuletItem.amulet_type_id]',  back_populates='amulet_type')


class AmuletItem(Base):
    """ Модель с амулетами в инвентаре пользователей """

    __tablename__ = 'amulets_in_inventory'
    id: Mapped[int] = mapped_column(primary_key=True)

    amulet_type_id: Mapped[int] = mapped_column(ForeignKey('amulet_types.id'), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=False)
    card_id: Mapped[int | None] = mapped_column(ForeignKey('cards.id', ondelete='SET NULL'), nullable=True)
    upgrades: Mapped[int] = mapped_column(Integer, default=0)

    amulet_type = relationship('AmuletType', foreign_keys=[amulet_type_id], back_populates='amulets_in_inventory')
    owner = relationship('Profile', foreign_keys=[owner_id],  back_populates='amulets')
    card = relationship('Card', foreign_keys=[card_id],  back_populates='amulet')


class UpgradeItemsType(Base):
    """ Модель типов предметов, позволяющих усиливать карты (ее параметры).
        Не изменяется системой, загружается через заполнение модели
    """

    __tablename__ = 'upgrade_items_types'
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=True)
    type: Mapped[str] = mapped_column(String(30), nullable=True)
    amount_up: Mapped[int] = mapped_column(Integer, nullable=True)
    image: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=True)
    price_of_use: Mapped[int] = mapped_column(Integer, nullable=True)

    user_items = relationship('UpgradeItemsUsers', foreign_keys='[UpgradeItemsUsers.upgrade_item_type_id]', back_populates='upgrade_item_type')


class UpgradeItemsUsers(Base):
    """ Модель предметов улучшения карт в инвентаре пользователей """

    __tablename__ = 'upgrade_items_users_in_inventory'
    id: Mapped[int] = mapped_column(primary_key=True)

    upgrade_item_type_id: Mapped[int] = mapped_column(ForeignKey('upgrade_items_types.id'), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=True)

    upgrade_item_type = relationship('UpgradeItemsType', foreign_keys=[upgrade_item_type_id], back_populates='user_items')
    owner = relationship('Profile', foreign_keys=[owner_id], back_populates='upgrade_items')


class Boxes(Base):
    """ Модель сундуков в магазине предметов """

    __tablename__ = 'boxes_in_store'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    image: Mapped[str] = mapped_column(String(255), nullable=True)
    reward_type: Mapped[str] = mapped_column(String(255), nullable=False)
    reward_amount: Mapped[int] = mapped_column(Integer, nullable=False)
