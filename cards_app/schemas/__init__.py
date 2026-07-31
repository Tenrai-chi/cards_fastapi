from .auth import *
from .base import CardBase, AmuletBase, ExpItemsBase, GuildBase, ProfileBase
from .cards import *
from .fight import *
from .inventory import *
from .news import *
from .profile import *
from .response import *
from .start_event import *
from .store import *
from .users import *


__all__ = [
    # ------ auth ------
    'UserRegister',
    'Token',
    'RefreshTokenRequest',

    # ------ base ------
    'CardBase',
    'AmuletBase',
    'ExpItemsBase',
    'GuildBase',
    'ProfileBase',

    # ------ cards ------
    'CardDTO',
    'OneCardForMergeDTO',
    'CardInfoDTO',
    'RarityCard',
    'ClassCard',
    'GetFreeCardDTO',
    'UserCardsDTO',
    'CardsTradingDTO',
    'CardsForMergeDTO',

    # ------ fight ------
    'Participant',
    'FightDTO',

    # ------ inventory ------
    'ExpItemsInventoryDTO',
    'AmuletsInventoryDTO',
    'UpgradeItemsInventoryDTO',
    'FullInventoryDTO',
    'CardLevelingDTO',
    'FullInfoLevelingDTO',
    'CardUpgradingDTO',
    'FullInfoUpgradingDTO',

    # ------ news ------
    'NewsRecordDTO',
    'NewsDTO',

    # ------ profile ------
    'UserRatingTableDTO',
    'RatingTableDTO',
    'FavoriteUserDTO',
    'FavoriteUsersPageDTO',
    'RecordTransaction',
    'TransactionsDTO',
    'FightHistoryRecordDTO',
    'ProfileFullInfoDTO',

    # ------ response ------
    'ViewCardUseCaseResponse',
    'ViewGetFreeCardUseCaseResponse',
    'GetFreeCardUseCaseResponse',
    'ViewUserCardsUseResponse',
    'ViewTradingUseCaseResponse',
    'ViewMergeUseCaseResponse',
    'MergeUseCaseResponse',
    'ViewUpgradeUseCaseResponse',
    'UpgradeUseCaseResponse',

    'ViewNewsUseCaseResponse',
    'ViewUsersRatingResponse',
    'ViewStartEventUseCaseResponse',
    'GetAwardStartEventUseCaseResponse',

    'ViewInventoryUseCaseResponse',
    'SaleAmuletUseCaseResponse',

    'ViewCardStoreUseCaseResponse',
    'ViewItemStoreUseCaseResponse',
    'BuyStoreCardUseCaseResponse',
    'BuyBoxUseCaseResponse',
    'BuyItemUseCaseResponse',

    'FavoriteUsersUseCaseResponse',
    'UserTransactionsUseCaseResponse',
    'ViewProfileUseCaseResponse',
    'ToggleFavoriteUserUseCaseResponse',

    'ProcessFightUseCaseResponse',

    # ------ start_event ------
    'StartEventAwardDTO',
    'StartEventAwardsDTO',

    # ------ store ------
    'CardInStoreDTO',
    'CardStoreDTO',
    'BoxStoreDTO',
    'ExpItemsStoreDTO',
    'AmuletsStoreDTO',
    'UpgradeItemsStoreDTO',
    'AllStoreDTO',
    'AmuletRewardDTO',

    # ------ users ------
    'UserOut',
    'CurrentUserForMenuDTO',
]
