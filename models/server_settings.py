# models/server_settings.py
from enum import Enum
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import pytz

class FeatureType(Enum):
    GACHA = "gacha"
    BATTLE = "battle"
    FORTUNE = "fortune"

@dataclass
class PointDistribution:
    item_type: str
    min_points: int
    max_points: int

@dataclass
class RoleCondition:
    type: str  # "points_threshold", "battle_wins", etc.
    value: int

@dataclass
class RoleSettings:
    role_id: str
    condition: RoleCondition

@dataclass
class MessageSettings:
    setup: str
    daily: str
    win: str
    custom_messages: Dict[str, str]

    def to_dict(self):
        return {
            'setup': self.setup,
            'daily': self.daily,
            'win': self.win,
            'custom_messages': self.custom_messages
        }

@dataclass
class MediaSettings:
    setup_image: Optional[str] = None
    banner_gif: Optional[str] = None

    def to_dict(self):
        return {
            'setup_image': self.setup_image,
            'banner_gif': self.banner_gif
        }

@dataclass
class GachaFeatureSettings:
    enabled: bool = True
    messages: Optional[MessageSettings] = None
    media: Optional[MediaSettings] = None
    points: List[PointDistribution] = None
    roles: List[RoleSettings] = None
    items: List[Dict] = None  # 既存のガチャアイテム設定を維持

@dataclass
class BattleFeatureSettings:
    enabled: bool = True
    required_role_id: Optional[str] = None
    winner_role_id: Optional[str] = None
    points_enabled: bool = True
    points_per_kill: int = 100
    winner_points: int = 1000
    start_delay_minutes: int = 2

@dataclass
class FortuneFeatureSettings:
    enabled: bool = True
    # 占い機能固有の設定をここに追加

@dataclass
class GlobalSettings:
    point_unit: str = "ポイント"
    timezone: str = "Asia/Tokyo"
    language: str = "ja"
    features_enabled: Dict[str, bool] = None

    def __post_init__(self):
        if self.features_enabled is None:
            self.features_enabled = {
                FeatureType.GACHA.value: True,
                FeatureType.BATTLE.value: True,
                FeatureType.FORTUNE.value: True
            }

@dataclass
class ServerSettings:
    server_id: str
    global_settings: GlobalSettings
    gacha_settings: GachaFeatureSettings
    battle_settings: BattleFeatureSettings
    fortune_settings: FortuneFeatureSettings
    updated_at: str = None
    version: int = 1

    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()

    def to_dict(self) -> dict:
        """設定をDynamoDBに保存可能な形式に変換"""
        return {
            'server_id': self.server_id,
            'global_settings': {
                'point_unit': self.global_settings.point_unit,
                'timezone': self.global_settings.timezone,
                'language': self.global_settings.language,
                'features_enabled': self.global_settings.features_enabled
            },
            'feature_settings': {
                'gacha': {
                    'enabled': self.gacha_settings.enabled,
                    'messages': self.gacha_settings.messages.to_dict() if self.gacha_settings.messages else None,
                    'media': self.gacha_settings.media.to_dict() if self.gacha_settings.media else None,
                    'points': [p.__dict__ for p in self.gacha_settings.points] if self.gacha_settings.points else None,
                    'roles': [r.__dict__ for r in self.gacha_settings.roles] if self.gacha_settings.roles else None,
                    'items': self.gacha_settings.items
                },
                'battle': {
                    'enabled': self.battle_settings.enabled,
                    'required_role_id': self.battle_settings.required_role_id,
                    'winner_role_id': self.battle_settings.winner_role_id,
                    'points_enabled': self.battle_settings.points_enabled,
                    'points_per_kill': self.battle_settings.points_per_kill,
                    'winner_points': self.battle_settings.winner_points,
                    'start_delay_minutes': self.battle_settings.start_delay_minutes
                },
                'fortune': {
                    'enabled': self.fortune_settings.enabled
                }
            },
            'updated_at': self.updated_at,
            'version': self.version
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ServerSettings':
        """DynamoDBから取得したデータをServerSettingsオブジェクトに変換"""
        if not data:
            return None

        global_settings = GlobalSettings(
            point_unit=data.get('global_settings', {}).get('point_unit', 'ポイント'),
            timezone=data.get('global_settings', {}).get('timezone', 'Asia/Tokyo'),
            language=data.get('global_settings', {}).get('language', 'ja'),
            features_enabled=data.get('global_settings', {}).get('features_enabled')
        )

        feature_settings = data.get('feature_settings', {})

        gacha_settings = GachaFeatureSettings(
            enabled=feature_settings.get('gacha', {}).get('enabled', True),
            messages=MessageSettings(
                **feature_settings.get('gacha', {}).get('messages', {})
            ) if feature_settings.get('gacha', {}).get('messages') else None,
            media=MediaSettings(
                **feature_settings.get('gacha', {}).get('media', {})
            ) if feature_settings.get('gacha', {}).get('media') else None,
            items=feature_settings.get('gacha', {}).get('items', [])
        )

        battle_settings = BattleFeatureSettings(
            enabled=feature_settings.get('battle', {}).get('enabled', True),
            required_role_id=feature_settings.get('battle', {}).get('required_role_id'),
            winner_role_id=feature_settings.get('battle', {}).get('winner_role_id'),
            points_enabled=feature_settings.get('battle', {}).get('points_enabled', True),
            points_per_kill=feature_settings.get('battle', {}).get('points_per_kill', 100),
            winner_points=feature_settings.get('battle', {}).get('winner_points', 1000),
            start_delay_minutes=feature_settings.get('battle', {}).get('start_delay_minutes', 2)
        )

        fortune_settings = FortuneFeatureSettings(
            enabled=feature_settings.get('fortune', {}).get('enabled', True)
        )

        return cls(
            server_id=data['server_id'],
            global_settings=global_settings,
            gacha_settings=gacha_settings,
            battle_settings=battle_settings,
            fortune_settings=fortune_settings,
            updated_at=data.get('updated_at'),
            version=data.get('version', 1)
        )
