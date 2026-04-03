from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey, Float, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class GuildBuff(Base):
    """ Модель с усилениями гильдии.
        Загружается через заполнение модели
    """

    __tablename__ = 'guild_buffs'
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    numeric_value: Mapped[float] = mapped_column(Float, nullable=False)

    guilds = relationship('Guild', foreign_keys='[Guild.buff_id]',  back_populates='buff')


class Guild(Base):
    """ Модель со списком гильдий """

    __tablename__ = 'guilds'
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(75), unique=True, nullable=False, index=True)
    leader_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', use_alter=True), nullable=False)
    number_of_participants: Mapped[int] = mapped_column(Integer, default=1)
    max_number_of_participants: Mapped[int] = mapped_column(Integer, default=30)
    guild_pic: Mapped[str] = mapped_column(String(255), default='image/guild/avatar.png')
    date_create: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    buff_id: Mapped[int] = mapped_column(ForeignKey('guild_buffs.id'), nullable=False)
    date_last_change_buff: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    leader = relationship('Profile', foreign_keys=[leader_id], back_populates='leader_guild')
    buff = relationship('GuildBuff', foreign_keys=[buff_id], back_populates='guilds')
    members = relationship('Profile', foreign_keys='[Profile.guild_id]', back_populates='guild')

    __table_args__ = (
        CheckConstraint('number_of_participants BETWEEN 1 AND max_number_of_participants', name='check_amount_members'),
        CheckConstraint('rating >= 0', name='check_rating'),
    )
