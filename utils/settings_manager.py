from models.server_settings import ServerSettings, GachaFeatureSettings, BattleFeatureSettings, FortuneFeatureSettings
from models.server_settings import MessageSettings, MediaSettings
from typing import Optional, Dict, Any
import copy

class ServerSettingsManager:
    def __init__(self, db):
        self.db = db
        self.settings_cache = {}

    async def get_settings(self, server_id: str) -> Optional[ServerSettings]:
        """サーバー設定を取得"""
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
            # 現在の設定を取得
            current_settings = await self.get_settings(server_id)
            if not current_settings:
                return False

            # 設定をディープコピー
            updated_settings = copy.deepcopy(current_settings)

            # 機能別の設定を更新
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
            success = await self.db.update_server_settings(server_id, settings.to_dict())
            if success:
                self.settings_cache[server_id] = settings
            return success
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False

    def _create_default_settings(self, server_id: str) -> ServerSettings:
        """デフォルトのサーバー設定を作成"""
        default_messages = MessageSettings(
            setup='ガチャへようこそ！\nここではさまざまなアイテムを獲得できます。',
            daily='{user}さんがガチャを引きました！',
            win='おめでとうございます！{user}さんが{item}を獲得しました！',
            custom_messages={}
        )
        
        default_media = MediaSettings(
            setup_image=None,
            banner_gif=None
        )

        return ServerSettings(
            server_id=server_id,
            global_settings=None,  # デフォルト値はServerSettingsクラスで設定
            gacha_settings=GachaFeatureSettings(
                enabled=True,
                messages=default_messages,
                media=default_media,
                items=[]
            ),
            battle_settings=BattleFeatureSettings(),
            fortune_settings=FortuneFeatureSettings()
        )