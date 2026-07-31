from .auth import *
from .cards import *
from .events import *
from .fight import *
from .guild import *
from .inventory import *
from .profile import *
from .store import *
from .users import *

__all__ = [
    # ------ auth ------
    'create_user_and_profile',
    'authenticate_and_create_tokens',
    
    # ------ cards ------
    'get_card_with_details',
    'get_rarities_and_classes',
    'generate_random_card',
    'generate_card_start_event',
    'create_new_card_from_template',
    'get_temp_card_in_store',
    'get_all_cards_user',
    'create_record_in_history_receiving_card',
    'update_card_experience',
    'increase_stats',
    'get_cards_in_trading',
    'get_cards_for_merge',
    'increase_merger',
    'merge_card',
    'clear_owner_card',
    'generate_max_stat_ur_card',
        
    # ------ events ------
    'get_paginated_news',
    'get_total_news_count',
    'get_info_start_event_awards',
    'can_get_start_event_award',
    'update_profile_event_award_received',
    'get_info_award',
        
    # ------ fight ------
    'validate_battle_preconditions',
    'check_last_fight',
    'get_cards_participants',
    'stats_calculation',
    'fight_now',
    'process_turn',
    'use_spell_dryad',
    'use_spell_demon',
    'use_spell_werewolf',
    'use_spell_ghost',
    'use_spell_emperor_mankind',
    'use_spell_berserk',
    'use_spell_reaper',
    'formation_of_history',
    'create_record_fight_history',
        
    # ------ guild ------
    'update_guild_points_user',
        
    # ------ inventory ------
    'add_experience_books_batch',
    'add_upgrade_item_to_user',
    'can_user_receive_amulet',
    'get_all_amulets_user',
    'give_amulets_to_user_butch',
    'delete_amulet',
    'remove_amulet_from_card',
    'reward_loot_after_fight',
    'get_all_types_amulets',
    'get_all_exp_items',
    'get_exp_items_in_user_inventory',
    'get_upgrade_items_in_user_inventory',
    'get_upgrade_item_in_inventory',
    'get_amulets_in_user_inventory',
    'upgrade_card_stats_and_level',
    'upgrade_card',
        
    # ------ profile ------
    'get_base_info_profile',
    'get_battle_stats',
    'get_user_fight_history',
    'is_favorite',
    'update_user_receiving_timer',
    'check_can_user_receive_card',
    'charge_user_gold',
    'add_user_gold',
    'create_transaction',
    'add_user_to_favorite',
    'remove_user_from_favorite',
    'ensure_favorite_slot_available',
    'get_favorite_user',
    'update_win_lose',
    'add_gold_for_fight',
    'update_rating_user',
    'get_rating_users',
    'get_total_users_count',
    'get_user_transactions',
        
    # ------ store ------
    'get_cards_in_store',
    'get_box_in_store',
    'get_amulets_in_store',
    'get_amulet_by_name',
    'get_upgrade_items_in_store',
    'get_exp_items_in_store',
    'get_box_info',
    'open_box_card',
    'open_box_exp_item',
    'open_box_amulet',
    'buy_exp_items',
    'buy_amulet',
    'buy_upgrade_item',
    'get_book_by_name',
        
    # ------ users ------
    'user_info_to_dto',
    'get_user_with_profile',
    'get_profile_for_update',
]
