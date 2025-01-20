# models/server_settings.py
from enum import Enum
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import pytz

class FeatureType(Enum):
    GACHA = "gacha"
    BATTLE = "battle"
    FORTUNE = "fortune"
    POINT_CONSUMPTION = "point_consumption"  # 追加

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
    custom_messages: Dict[str, str] = None  # デフォルト値を None に設定
    tweet_message: Optional[str] = None  # 追加: X投稿用メッセージ

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
    gacha_animation_gif: Optional[str] = None  # 新しく追加

    def to_dict(self):
        return {
            'setup_image': self.setup_image,
            'banner_gif': self.banner_gif,
            'gacha_animation_gif': self.gacha_animation_gif  # 追加
        }

@dataclass
class GachaFeatureSettings:
    enabled: bool = True
    messages: Optional[MessageSettings] = None
    media: Optional[MediaSettings] = None
    points: List[PointDistribution] = None
    roles: List[RoleSettings] = None
    items: List[Dict] = None  # 既存のガチャアイテム設定を維持
    use_daily_panel: bool = True  # 新しく追加

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
class PointConsumptionModalSettings:
    title: str = "ポイント消費申請"
    fields: Dict[str, bool] = field(default_factory=lambda: {
        "points": True,      # 必須フィールド
        "wallet": False,      # オプショナル
        "email": False       # オプショナル
    })
    field_labels: Dict[str, str] = field(default_factory=lambda: {
        "points": "消費ポイント",
        "wallet": "ウォレットアドレス",
        "email": "メールアドレス"
    })
    field_placeholders: Dict[str, str] = field(default_factory=lambda: {
        "points": "消費するポイント数を入力",
        "wallet": "0x...",
        "email": "example@example.com"
    })
    validation: Dict[str, Dict] = field(default_factory=lambda: {
        "points": {"min": 0, "max": None},
        "wallet": {"pattern": "^0x[a-fA-F0-9]{40}$"},
        "email": {"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"}
    })
    success_message: str = "申請を送信しました。"  # 新しい属性を追加

# 新しい設定クラスを追加
@dataclass
class PointConsumptionFeatureSettings:
    enabled: bool = True
    button_name: str = "ポイント消費"
    channel_id: Optional[str] = None
    notification_channel_id: Optional[str] = None
    mention_role_ids: List[str] = None
    use_thread: bool = False
    completion_message_enabled: bool = True
    required_points: int = 0
    panel_message: str = "ポイント消費パネル"
    thread_welcome_message: str = "{user}こちらからポイント消費申請を行ってください\nあなたの申請可能ポイントは{points}{unit}です"
    notification_message: str = "{user}が{points}{unit}の申請をしました"
    modal_settings: PointConsumptionModalSettings = None

    # 承認権限の設定を追加
    approval_roles: List[str] = field(default_factory=list)  # 承認可能なロールIDのリスト
    admin_override: bool = True  # 管理者は常に承認可能

    # ログ設定を追加
    history_channel_id: Optional[str] = None
    history_enabled: bool = False
    history_format: str = "{user}が{points}{unit}を消費しました\nステータス: {status}"

    logging_enabled: bool = False
    logging_channel_id: Optional[str] = None
    logging_actions: List[str] = None
    gain_history_enabled: bool = False
    gain_history_channel_id: Optional[str] = None
    consumption_history_enabled: bool = False
    consumption_history_channel_id: Optional[str] = None

    # パネルメッセージ設定を追加
    panel_message: str = "クリックしてポイントの消費申請をしてください"  # デフォルトメッセージ
    panel_title: str = "ポイント消費"  # タイトルも設定可能に

    # 新しい属性
    completion_message: str = "{user}が{points}{unit}を消費しました。管理者: {admin}"

    def __post_init__(self):
        if self.mention_role_ids is None:
            self.mention_role_ids = []
        if self.logging_actions is None:
            self.logging_actions = []
        if self.modal_settings is None:
            self.modal_settings = PointConsumptionModalSettings()  # デフォルト値を使用して初期化

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
    point_consumption_settings: PointConsumptionFeatureSettings  # 追加
    updated_at: str = None
    version: int = 1

    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
        if self.point_consumption_settings is None:  # 追加
            self.point_consumption_settings = PointConsumptionFeatureSettings()

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
                },
                'point_consumption': {
                    'enabled': self.point_consumption_settings.enabled,
                    'button_name': self.point_consumption_settings.button_name,
                    'channel_id': self.point_consumption_settings.channel_id,
                    'notification_channel_id': self.point_consumption_settings.notification_channel_id,
                    'mention_role_ids': self.point_consumption_settings.mention_role_ids,
                    'use_thread': self.point_consumption_settings.use_thread,
                    'completion_message_enabled': self.point_consumption_settings.completion_message_enabled,
                    'required_points': self.point_consumption_settings.required_points,
                    'logging_enabled': self.point_consumption_settings.logging_enabled,
                    'logging_channel_id': self.point_consumption_settings.logging_channel_id,
                    'logging_actions': self.point_consumption_settings.logging_actions,
                    'gain_history_enabled': self.point_consumption_settings.gain_history_enabled,
                    'gain_history_channel_id': self.point_consumption_settings.gain_history_channel_id,
                    'consumption_history_enabled': self.point_consumption_settings.consumption_history_enabled,
                    'consumption_history_channel_id': self.point_consumption_settings.consumption_history_channel_id
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

        # from_dict メソッド内の gacha_settings 部分を修正
        gacha_settings = GachaFeatureSettings(
            enabled=feature_settings.get('gacha', {}).get('enabled', True),
            messages=MessageSettings(
                setup='**ガチャを回して運試し！**\n1日1回ガチャが回せるよ！',
                daily='1日1回ガチャが回せます！\n下のボタンを押してガチャを実行してください。',
                win='',
                custom_messages={}
            ) if not feature_settings.get('gacha', {}).get('messages') else MessageSettings(
                **feature_settings.get('gacha', {}).get('messages', {})
            ),
            media=MediaSettings(
                setup_image='',
                banner_gif=''
            ) if not feature_settings.get('gacha', {}).get('media') else MediaSettings(
                **feature_settings.get('gacha', {}).get('media', {})
            ),
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

        # ポイント消費設定を追加
        point_consumption_data = feature_settings.get('point_consumption', {})

        point_consumption_settings = PointConsumptionFeatureSettings(
            enabled=point_consumption_data.get('enabled', True),
            button_name=point_consumption_data.get('button_name', "ポイント消費"),
            channel_id=point_consumption_data.get('channel_id'),
            notification_channel_id=point_consumption_data.get('notification_channel_id'),
            mention_role_ids=point_consumption_data.get('mention_role_ids', []),
            use_thread=point_consumption_data.get('use_thread', False),
            completion_message_enabled=point_consumption_data.get('completion_message_enabled', True),
            required_points=point_consumption_data.get('required_points', 0),
            
            panel_message=point_consumption_data.get('panel_message', "クリックしてポイントの消費申請をしてください"),
            panel_title=point_consumption_data.get('panel_title', "ポイント消費"),
            thread_welcome_message=point_consumption_data.get('thread_welcome_message', "{user}こちらからポイント消費申請を行ってください\nあなたの申請可能ポイントは{points}{unit}です"),
            notification_message=point_consumption_data.get('notification_message', "{user}が{points}{unit}の申請をしました"),
            completion_message=point_consumption_data.get('completion_message', "{user}が{points}{unit}を消費しました。管理者: {admin}"),
            logging_enabled=point_consumption_data.get('logging_enabled', False),
            logging_channel_id=point_consumption_data.get('logging_channel_id'),
            logging_actions=point_consumption_data.get('logging_actions', []),
            gain_history_enabled=point_consumption_data.get('gain_history_enabled', False),
            gain_history_channel_id=point_consumption_data.get('gain_history_channel_id'),
            consumption_history_enabled=point_consumption_data.get('consumption_history_enabled', False),
            consumption_history_channel_id=point_consumption_data.get('consumption_history_channel_id')
        )

        return cls(
            server_id=data['server_id'],
            global_settings=global_settings,
            gacha_settings=gacha_settings,
            battle_settings=battle_settings,
            fortune_settings=fortune_settings,
            point_consumption_settings=point_consumption_settings,  # 追加
            updated_at=data.get('updated_at'),
            version=data.get('version', 1)
        )

