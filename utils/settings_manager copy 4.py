from models.server_settings import ServerSettings, GachaFeatureSettings, BattleFeatureSettings, FortuneFeatureSettings
from models.server_settings import MessageSettings, MediaSettings
from typing import Optional, Dict, Any
import copy
from datetime import datetime
import pytz
from decimal import Decimal

class ServerSettingsManager:
    def __init__(self, db):
        self.db = db
        self.settings_cache = {}

    async def get_settings(self, server_id: str) -> Optional[ServerSettings]:
        """サーバー設定を取得"""
        # キャッシュチェックは一時的にコメントアウト
        # if server_id in self.settings_cache:
        #     return self.settings_cache[server_id]

        settings_data = await self.db.get_server_settings(server_id)
        if not settings_data:
            settings = self._create_default_settings(server_id)
        else:
            settings = ServerSettings.from_dict(settings_data)

        self.settings_cache[server_id] = settings
        return settings

    async def update_feature_settings(self, server_id: str, feature: str, new_settings: Dict[str, Any]) -> bool:
        """機能別の設定を更新"""
        try:
            current_settings = await self.get_settings(server_id)
            if not current_settings:
                return False

            updated_settings = copy.deepcopy(current_settings)

            if feature == 'gacha':
                messages = MessageSettings(**new_settings['messages']) if new_settings.get('messages') else None
                media = MediaSettings(**new_settings['media']) if new_settings.get('media') else None
                
                updated_settings.gacha_settings = GachaFeatureSettings(
                    enabled=new_settings.get('enabled', True),
                    messages=messages,
                    media=media,
                    items=new_settings.get('items', [])
                )
            elif feature == 'battle':
                updated_settings.battle_settings = BattleFeatureSettings(**new_settings)
            elif feature == 'fortune':
                updated_settings.fortune_settings = FortuneFeatureSettings(**new_settings)
            else:
                return False

            success = await self.db.update_server_settings(server_id, updated_settings.to_dict())
            if success:
                self.settings_cache[server_id] = updated_settings
            return success

        except Exception as e:
            print(f"Error updating feature settings: {e}")
            return False

    async def update_settings(self, server_id: str, settings: ServerSettings) -> bool:
        """サーバー設定全体を更新"""
        try:
            success = await self.db.update_server_settings(server_id, settings.to_dict())
            if success:
                self.settings_cache[server_id] = settings
            return success
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False

    async def create_default_settings(self, server_id: str) -> bool:
        """デフォルト設定を作成して保存"""
        try:
            settings = self._create_default_settings(server_id)
            success = await self.db.update_server_settings(server_id, settings.to_dict())
            if success:
                self.settings_cache[server_id] = settings
            return success
        except Exception as e:
            print(f"Error creating default settings: {e}")
            return False
        
    def _create_default_settings(self, server_id: str) -> ServerSettings:
            """デフォルトのサーバー設定を作成"""
            default_messages = MessageSettings(
                setup='**ガチャを回して運試し！**\n1日1回ガチャが回せるよ！',
                daily='1日1回ガチャが回せます！\n下のボタンを押してガチャを実行してください。',
                win=None,
                tweet_message=None,
                custom_messages={}
            )
            
            default_media = MediaSettings(
                setup_image='https://nft-mint.xyz/gacha/gacha1.png',
                banner_gif='https://nft-mint.xyz/gacha/gacha1.gif',
                gacha_animation_gif='https://nft-mint.xyz/gacha/gacha1.gif'
            )

            default_gacha_items = [
                {
                    'name': 'URアイテム',
                    'weight': Decimal('2'),
                    'points': Decimal('200'),
                    'image_url': 'https://nft-mint.xyz/gacha/ur.png',
                    'message_settings': {
                        'enabled': True,
                        'message': '{item}を獲得しました！🎊✨'
                    }
                },
                {
                    'name': 'SSRアイテム',
                    'weight': Decimal('5'),
                    'points': Decimal('100'),
                    'image_url': 'https://nft-mint.xyz/gacha/ssr.png',
                    'message_settings': {
                        'enabled': True,
                        'message': '{item}を獲得しました！🎉'
                    }
                },
                {
                    'name': 'SRアイテム',
                    'weight': Decimal('15'),
                    'points': Decimal('50'),
                    'image_url': 'https://nft-mint.xyz/gacha/sr.png',
                    'message_settings': {
                        'enabled': True,
                        'message': '{item}です！✨'
                    }
                },
                {
                    'name': 'Rアイテム',
                    'weight': Decimal('30'),
                    'points': Decimal('30'),
                    'image_url': 'https://nft-mint.xyz/gacha/r.png',
                    'message_settings': {
                        'enabled': True,
                        'message': '{item}を引きました！'
                    }
                },
                {
                    'name': 'Nアイテム',
                    'weight': Decimal('48'),
                    'points': Decimal('10'),
                    'image_url': 'https://nft-mint.xyz/gacha/n.png',
                    'message_settings': {
                        'enabled': False,
                        'message': '{item}です'
                    }
                }
            ]

            return ServerSettings(
                server_id=server_id,
                global_settings={
                    'point_unit': 'ポイント',
                    'timezone': 'Asia/Tokyo',
                    'language': 'ja',
                    'features_enabled': {
                        'gacha': True,
                        'battle': True,
                        'fortune': True,
                        'rewards': True,
                        'daily_point_limit': Decimal('0'),
                        'notifications': {
                            'ranking_updated': True,
                            'points_earned': True
                        }
                    }
                },
                gacha_settings=GachaFeatureSettings(
                    enabled=True,
                    messages=default_messages,
                    media=default_media,
                    items=default_gacha_items,
                    use_daily_panel=False
                ),
                battle_settings=BattleFeatureSettings(
                    enabled=True,
                    required_role_id=None,
                    winner_role_id=None,
                    points_enabled=True,
                    points_per_kill=Decimal('10'),
                    winner_points=Decimal('100'),
                    start_delay_minutes=Decimal('2')
                ),
                fortune_settings=FortuneFeatureSettings(
                    enabled=True,
                    custom_messages={}
                ),
                rewards_settings={
                    'enabled': True,
                    'web3': {
                        'rpc_url': '',
                        'private_key': '',
                        'nft_contract_address': '',
                        'token_contract_address': ''
                    },
                    'coupon_api': {
                        'api_key': '',
                        'api_url': ''
                    },
                    'limits': {
                        'min_points_coupon': Decimal('100'),
                        'max_points_coupon': Decimal('1000'),
                        'min_points_nft': Decimal('1000'),
                        'min_points_token': Decimal('500'),
                        'token_conversion_rate': Decimal('0.1')
                    }
                },
                point_consumption_settings={
                    'enabled': True,
                    'button_name': "ポイント消費",
                    'channel_id': None,
                    'notification_channel_id': None,
                    'mention_role_ids': [],
                    'use_thread': False,
                    'completion_message_enabled': True,
                    'required_points': Decimal('0'),
                    'gain_history_enabled': False,
                    'gain_history_channel_id': None,
                    'consumption_history_enabled': False,
                    'consumption_history_channel_id': None,
                    'logging_enabled': True,
                    'logging_channel_id': None,
                    'display_channel_id': None,
                    'logging_actions': ['click', 'complete', 'cancel']
                },
                version=Decimal('1')
            )