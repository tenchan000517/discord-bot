from models.server_settings import ServerSettings, GachaFeatureSettings, BattleFeatureSettings, FortuneFeatureSettings, PointConsumptionFeatureSettings, PointConsumptionModalSettings
from models.server_settings import MessageSettings, MediaSettings, GachaSettings
from typing import Optional, Dict, Any
import copy
from decimal import Decimal
from utils.default_settings import create_default_settings

class ServerSettingsManager:
    def __init__(self, db):
        self.db = db
        self.settings_cache = {}

    async def get_settings(self, server_id: str) -> Optional[ServerSettings]:
        """サーバー設定を取得"""
        settings_data = await self.db.get_server_settings(server_id)

        if not settings_data:
            # デフォルト設定は作成せず、Noneを返す
            return None
        
        settings = ServerSettings.from_dict(settings_data)
        self.settings_cache[server_id] = settings
        return settings

    async def update_feature_settings(self, server_id: str, feature: str, new_settings: Dict[str, Any]) -> bool:
        """機能別の設定を更新
        
        cogs\modals.py

        cogs\settings\modals\base.py
        cogs\settings\modals\battle_settings.py
        cogs\settings\modals\fortunes_settings.py
        cogs\settings\modals\gacha_items.py
        cogs\settings\modals\gacha_settings.py
        cogs\settings\modals\global_settings.py

        cogs\settings\views\gacha_view.py
        cogs\settings\views\settings_view.py
        
        """
        try:
            # 現在の設定を取得
            current_settings = await self.get_settings(server_id)
            if not current_settings:
                return False

            # 設定をディープコピー
            updated_settings = copy.deepcopy(current_settings)

            # 機能別の設定を更新
            if feature == 'gacha':
                messages = MessageSettings(
                    setup=new_settings['messages'].get('setup', ''),  # デフォルト値を設定
                    daily=new_settings['messages'].get('daily', ''),  # デフォルト値を設定
                    win=new_settings['messages'].get('win', ''),  # デフォルト値を設定
                    custom_messages=new_settings['messages'].get('custom_messages', {})  # デフォルト値を設定
                ) if new_settings.get('messages') else None
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
            elif feature == 'point_consumption':
                modal_settings = PointConsumptionModalSettings(**new_settings.get('modal_settings', {})) if new_settings.get('modal_settings') else None
                updated_settings.point_consumption_settings = PointConsumptionFeatureSettings(
                    **{**new_settings, 'modal_settings': modal_settings}
                )  
            else:
                return False

            # DynamoDBに保存
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
            # print(f"[DEBUG] Type of settings in update_settings: {type(settings)}")
            # print(f"[DEBUG] settings in update_settings: {settings}")

            success = await self.db.update_server_settings(server_id, settings.to_dict())

            if isinstance(settings, ServerSettings):
                settings_dict = settings.to_dict()
                print(f"[DEBUG] settings.to_dict() result: {settings_dict}")
            else:
                print("[ERROR] settings is not a ServerSettings object")

            if success:
                self.settings_cache[server_id] = settings
            return success
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False
        
    # ボット招待後２番目に仕事する aws_databaseのonguild_serverより呼び出される
    async def create_default_settings(self, server_id: str) -> bool:
        """デフォルト設定を作成して保存"""
        try:
            # デフォルト設定を生成
            settings = self._create_default_settings(server_id)
            
            # 設定を保存
            success = await self.db.update_server_settings(server_id, settings.to_dict())
            if success:
                self.settings_cache[server_id] = settings
            return success
        except Exception as e:
            print(f"Error creating default settings: {e}")
            return False
    
    def _create_default_settings(self, server_id: str) -> ServerSettings:
        """デフォルトのサーバー設定を作成"""
        settings_dict = create_default_settings(server_id)
        return ServerSettings.from_dict(settings_dict)