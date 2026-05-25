from datetime import datetime

from sqlalchemy import Integer, String, Boolean, DateTime, Text, ForeignKey, BigInteger, Date, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func

from .base import Base


class User(Base):
    """ Модель пользователей с полями с системными полями.
        Базовые данные и данные для аутентификации.
        Эта модель первостепенная, однако остальные сущности связаны к Профилю
    """

    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    date_joined: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    first_name: Mapped[str] = mapped_column(String(150), nullable=True)
    last_name: Mapped[str] = mapped_column(String(150), nullable=True)
    pending_email: Mapped[str] = mapped_column(String(254), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    profile = relationship('Profile', foreign_keys='[Profile.user_id]', back_populates='user', uselist=False, cascade='all, delete-orphan')
    refresh_tokens = relationship('RefreshToken', back_populates='user')


class Profile(Base):
    """ Модель профилей пользователей.
        Данные пользователей для взаимодействия с сайтом.
    """

    __tablename__ = 'profiles'
    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True, nullable=False)
    about_user: Mapped[str] = mapped_column(Text, nullable=True)
    gold: Mapped[int] = mapped_column(BigInteger, default=10000, nullable=False)
    diamond: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    receiving_timer: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    win: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lose: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_card_id: Mapped[int] = mapped_column(ForeignKey('cards.id'), nullable=True)

    profile_pic: Mapped[str] = mapped_column(String(255), default='image/profile/avatar_default.png', nullable=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey('guilds.id'), nullable=True)
    date_guild_accession: Mapped[Date] = mapped_column(Date, nullable=True)
    guild_point: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    card_slots: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    amulet_slots: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    experience_bar: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    event_visit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    date_event_visit: Mapped[Date] = mapped_column(Date, nullable=True)
    rating: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    max_favorite: Mapped[int] = mapped_column(Integer, default=50)

    user = relationship('User', foreign_keys=[user_id], back_populates='profile')
    current_card = relationship('Card', foreign_keys=[current_card_id], back_populates='selected_by')
    guild = relationship('Guild', foreign_keys=[guild_id], back_populates='members')
    leader_guild = relationship('Guild', foreign_keys='[Guild.leader_id]', back_populates='leader', uselist=False)

    cards = relationship('Card', foreign_keys='[Card.owner_id]', back_populates='owner')
    fights_as_participant1 = relationship('FightHistory',
                                          foreign_keys='[FightHistory.participant1_id]',
                                          back_populates='participant1'
                                          )
    fights_as_participant2 = relationship('FightHistory',
                                          foreign_keys='[FightHistory.participant2_id]',
                                          back_populates='participant2'
                                          )
    fights_won = relationship('FightHistory',
                              foreign_keys='FightHistory.winner_id',
                              back_populates='winner'
                              )

    cards_received = relationship('HistoryReceivingCards', foreign_keys='[HistoryReceivingCards.user_id]',
                                  back_populates='user')
    favorites = relationship('FavoriteUsers', foreign_keys='[FavoriteUsers.user_id]', back_populates='user')
    favored_by = relationship('FavoriteUsers', foreign_keys='[FavoriteUsers.favorite_user_id]',
                              back_populates='favorite_user')
    transactions = relationship('Transactions', foreign_keys='[Transactions.user_id]', back_populates='user')
    purchases = relationship('SaleUserCards', foreign_keys='[SaleUserCards.buyer_id]', back_populates='buyer')
    sales = relationship('SaleUserCards', foreign_keys='[SaleUserCards.salesman_id]', back_populates='salesman')
    inventory = relationship('UsersInventory', foreign_keys='[UsersInventory.owner_id]', back_populates='owner')
    purchased_items = relationship('HistoryPurchaseItems', foreign_keys='[HistoryPurchaseItems.user_id]',
                                   back_populates='user')
    amulets = relationship('AmuletItem', foreign_keys='[AmuletItem.owner_id]', back_populates='owner')
    upgrade_items = relationship('UpgradeItemsUsers', foreign_keys='[UpgradeItemsUsers.owner_id]',
                                 back_populates='owner')
    battle_template = relationship('TeamsForBattleEvent', foreign_keys='[TeamsForBattleEvent.user_id]',
                                   back_populates='user', uselist=False)
    battle_participant = relationship('BattleEventParticipants', foreign_keys='[BattleEventParticipants.user_id]',
                                      back_populates='user', uselist=False)

    __table_args__ = (
        CheckConstraint('rating >= 0', name='check_rating_non_negative'),
    )

    @validates('rating')
    def validate_rating(self, key, value):
        return max(0, value)


class FavoriteUsers(Base):
    """ Модель со списком избранных пользователей у пользователей """

    __tablename__ = 'favorite_users'
    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=False)
    favorite_user_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=False)

    user = relationship('Profile', foreign_keys=[user_id], back_populates='favorites')
    favorite_user = relationship('Profile', foreign_keys=[favorite_user_id], back_populates='favored_by')


class Transactions(Base):
    """ Модель с транзакциями пользователей """

    __tablename__ = 'transactions'
    id: Mapped[int] = mapped_column(primary_key=True)

    date_and_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=False)
    before: Mapped[int] = mapped_column(Integer, nullable=False)
    after: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(String(300), nullable=False)

    user = relationship('Profile', foreign_keys=[user_id],  back_populates='transactions')
    buyer_transactions = relationship('SaleUserCards', foreign_keys='[SaleUserCards.transaction_buyer_id]',
                                      back_populates='transaction_buyer')
    seller_transactions = relationship('SaleUserCards', foreign_keys='[SaleUserCards.transaction_salesman_id]',
                                       back_populates='transaction_salesman')
    item_purchases = relationship('HistoryPurchaseItems', foreign_keys='[HistoryPurchaseItems.transaction_id]',
                                  back_populates='transaction')


class FightHistory(Base):
    """ Модель с историей рейтинговых боев """

    __tablename__ = 'fight_history'
    id: Mapped[int] = mapped_column(primary_key=True)

    date_and_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_victory: Mapped[bool] = mapped_column(Boolean)
    participant1_id: Mapped[int] = mapped_column(ForeignKey('profiles.id'), nullable=False)
    participant2_id: Mapped[int] = mapped_column(ForeignKey('profiles.id'), nullable=False)
    winner_id: Mapped[int] = mapped_column(ForeignKey('profiles.id'), nullable=True)

    card1_id: Mapped[int] = mapped_column(ForeignKey('cards.id'), nullable=False)
    card2_id: Mapped[int] = mapped_column(ForeignKey('cards.id'), nullable=False)

    participant1 = relationship('Profile', foreign_keys=[participant1_id], back_populates='fights_as_participant1')
    participant2 = relationship('Profile', foreign_keys=[participant2_id], back_populates='fights_as_participant2')
    winner = relationship('Profile', foreign_keys=[winner_id], back_populates='fights_won')
    card1 = relationship('Card', foreign_keys=[card1_id], back_populates='fight_histories_as_card1')
    card2 = relationship('Card', foreign_keys=[card2_id], back_populates='fight_histories_as_card2')


class RefreshToken(Base):
    """ Токины пользователей для сессий.
        Позволяет:
        - Отзывать токен при выходе из сессии (токен удаляется)
        - Добавлять новый токе сессии (при входе создается новый)
        - Делать проверку на валидность токена при обновлении access-токена
        - Управлять активными сессиями
    """

    __tablename__ = 'refresh_tokens'
    id: Mapped[int] = mapped_column(primary_key=True)

    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now())

    user = relationship('User', back_populates='refresh_tokens')
