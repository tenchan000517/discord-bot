# utils/settings_manager.py
from typing import Optional, Dict, Any
from models.server_settings import ServerSettings, GlobalSettings, GachaFeatureSettings, BattleFeatureSettings, FortuneFeatureSettings
from datetime import datetime
import pytz
import json

class ServerSettingsManager:
    def __init__(self, db):
        self.db = db
        self._cache = {}  # サーバーIDをキーとした設定のキャッシュ
        self._cache_timeout = 300  # キャッシュの有効期限（秒）
        self._cache_timestamps = {}  # キャッシュのタイムスタンプ

    def _get_cached_settings(self, server_id: str) -> Optional[ServerSettings]:
        """キャッシュされた設定を取得"""
        if server_id in self._cache:
            timestamp = self._cache_timestamps.get(server_id, 0)
            if (datetime.now().timestamp() - timestamp) < self._cache_timeout:
                return self._cache[server_id]
            else:
                # キャッシュの有効期限切れ
                del self._cache[server_id]
                del self._cache_timestamps[server_id]
        return None

    def _set_cached_settings(self, server_id: str, settings: ServerSettings):
        """設定をキャッシュに保存"""
        self._cache[server_id] = settings
        self._cache_timestamps[server_id] = datetime.now().timestamp()

    def get_settings(self, server_id: str) -> ServerSettings:
        """サーバーの設定を取得"""
        # まずキャッシュをチェック
        cached_settings = self._get_cached_settings(server_id)
        if cached_settings:
            return cached_settings

        # データベースから設定を取得
        try:
            data = self.db.get_server_settings(server_id)
            settings = ServerSettings.from_dict(data) if data else self._create_default_settings(server_id)
            
            # キャッシュに保存
            self._set_cached_settings(server_id, settings)
            
            return settings
        except Exception as e:
            print(f"Error getting server settings: {e}")
            return self._create_default_settings(server_id)

    def _create_default_settings(self, server_id: str) -> ServerSettings:
        """デフォルトの設定を作成"""
        return ServerSettings(
            server_id=server_id,
            global_settings=GlobalSettings(),
            gacha_settings=GachaFeatureSettings(
                items=[  # デフォルトのガチャアイテム
                    {
                        'name': 'SSRアイテム',
                        'weight': 5,
                        'points': 100,
                        'image_url': ''
                    },
                    {
                        'name': 'SRアイテム',
                        'weight': 15,
                        'points': 50,
                        'image_url': ''
                    },
                    {
                        'name': 'Rアイテム',
                        'weight': 30,
                        'points': 30,
                        'image_url': ''
                    },
                    {
                        'name': 'Nアイテム',
                        'weight': 50,
                        'points': 10,
                        'image_url': ''
                    }
                ]
            ),
            battle_settings=BattleFeatureSettings(),
            fortune_settings=FortuneFeatureSettings()
        )

    def update_settings(self, server_id: str, settings: ServerSettings) -> bool:
        """サーバーの設定を更新"""
        try:
            # 更新日時を設定
            settings.updated_at = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
            
            # 設定をDynamoDBに保存可能な形式に変換
            settings_dict = settings.to_dict()
            
            # データベースを更新
            success = self.db.update_server_settings(server_id, settings_dict)
            
            if success:
                # キャッシュを更新
                self._set_cached_settings(server_id, settings)
            
            return success
        except Exception as e:
            print(f"Error updating server settings: {e}")
            return False

    def update_feature_settings(self, server_id: str, feature: str, settings: Dict[str, Any]) -> bool:
        """特定の機能の設定のみを更新"""
        try:
            current_settings = self.get_settings(server_id)
            
            # 機能に応じて適切な設定を更新
            if feature == 'gacha':
                current_settings.gacha_settings = GachaFeatureSettings(**settings)
            elif feature == 'battle':
                current_settings.battle_settings = BattleFeatureSettings(**settings)
            elif feature == 'fortune':
                current_settings.fortune_settings = FortuneFeatureSettings(**settings)
            else:
                return False
            
            return self.update_settings(server_id, current_settings)
        except Exception as e:
            print(f"Error updating feature settings: {e}")
            return False

    def get_feature_settings(self, server_id: str, feature: str) -> Optional[Dict[str, Any]]:
        """特定の機能の設定のみを取得"""
        settings = self.get_settings(server_id)
        if not settings:
            return None

        if feature == 'gacha':
            return settings.gacha_settings
        elif feature == 'battle':
            return settings.battle_settings
        elif feature == 'fortune':
            return settings.fortune_settings
        
        return None