from .base import AppException

from .card import *
from .fight import *
from .inventory import *
from .resource import *
from .store import *
from .user import *

__all__ = [
    'AppException',

    'UserException',
    'UserNotFoundError',
    'CooldownNotElapsedError',
    'UserFavoriteException',
    'SelfFavoriteError',
    'SelfFavoriteRemoveError',
    'DuplicateFavoriteError',
    'FavoriteNotFoundError',

    'CardException',
    'CardNotFoundError',
    'NoCurrentCardError',

    'StoreException',
    'CardInStoreNotFoundError',
    'CardNotOnSaleError',

    'ResourceException',
    'InsufficientFundsUserError',

    'InventoryException',
    'NotEnoughSlotsError',

    'FightException',
    'SelfFightError',
]
