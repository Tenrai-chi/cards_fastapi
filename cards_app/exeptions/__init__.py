from .base import AppException

from .card import *
from .fight import *
from .inventory import *
from .resource import *
from .store import *
from .user import *

__all__ = [
    # ------ base ------
    'AppException',

    # ------ card ------
    'CardException',
    'CardNotFoundError',
    'NoCurrentCardError',
    'NotCardOwnerError',
    'EmptyCardsForMergeError',
    'TooManyCardsMergeError',
    'MaxUpgradeCardError',
    'SelfMergeError',

    # ------ fight ------
    'FightException',
    'SelfFightError',

    # ------ inventory ------
    'InventoryException',
    'NotEnoughSlotsError',
    'AmuletNotFoundError',
    'NotAmuletOwnerError',
    'NotEnoughUpgradeItemsError',

    # ------ resource ------
    'ResourceException',
    'InsufficientFundsUserError',

    # ------ store ------
    'StoreException',
    'CardInStoreNotFoundError',
    'CardNotOnSaleError',
    'BoxNotFoundError',
    'ExpItemNotFoundError',
    'AmuletNotFoundError',
    'AmuletNotOnSaleError',
    'UpgradeItemNotFoundError',

    # ------ user ------
    'UserException',
    'UserNotFoundError',
    'CooldownNotElapsedError',
    'UserFavoriteException',
    'SelfFavoriteError',
    'SelfFavoriteRemoveError',
    'DuplicateFavoriteError',
    'FavoriteNotFoundError',
]
