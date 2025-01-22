# models/server_settings.py
from enum import Enum
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import pytz
import uuid

class FeatureType(Enum):
    GACHA = "gacha"
    BATTLE = "battle"
    FORTUNE = "fortune"
    POINT_CONSUMPTION = "point_consumption"  # 追加

@dataclass
class PointUnit:
    unit_id: str
    name: str
    
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
    panel_title: str = "デイリーガチャ"  # パネルのタイトル
    button_labels: Dict[str, str] = field(default_factory=lambda: {
        'gacha': 'ガチャを回す！',
        'share': 'ガチャ結果をXに投稿',
        'points': 'ポイントを確認',
    })

    def to_dict(self):
        return {
            'setup': self.setup,
            'daily': self.daily,
            'win': self.win,
            'custom_messages': self.custom_messages,
            'tweet_message': self.tweet_message,
            'panel_title': self.panel_title,
            'button_labels': self.button_labels
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
class GachaSettings:
    gacha_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "デフォルトガチャ"
    channel_id: Optional[str] = None
    enabled: bool = True
    messages: Optional[MessageSettings] = None
    media: Optional[MediaSettings] = None
    items: List[Dict] = field(default_factory=list)
    roles: List[Dict] = field(default_factory=list)
    use_daily_panel: bool = True
    point_unit_id: str = "1"  # 追加: ポイント単位ID

    def to_dict(self) -> dict:
        return {
            'gacha_id': self.gacha_id,
            'name': self.name,
            'channel_id': self.channel_id,
            'enabled': self.enabled,
            'messages': self.messages.to_dict() if self.messages else None,
            'media': self.media.to_dict() if self.media else None,
            'items': self.items,
            'roles': self.roles,
            'use_daily_panel': self.use_daily_panel,
            'point_unit_id': self.point_unit_id  # 追加
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GachaSettings':
        return cls(
            gacha_id=data.get('gacha_id', str(uuid.uuid4())),
            name=data.get('name', 'デフォルトガチャ'),
            channel_id=data.get('channel_id'),
            enabled=data.get('enabled', True),
            messages=MessageSettings(**data['messages']) if data.get('messages') else None,
            media=MediaSettings(**data['media']) if data.get('media') else None,
            items=data.get('items', []),
            roles=data.get('roles', []),
            use_daily_panel=data.get('use_daily_panel', True),
            point_unit_id=data.get('point_unit_id', "1")  # 追加
        )

@dataclass
class GachaFeatureSettings:
    enabled: bool = True
    gacha_list: List[GachaSettings] = field(default_factory=list)
    points: List[PointDistribution] = field(default_factory=list)  # 保持
    roles: List[RoleSettings] = field(default_factory=list)  # 保持

    def __post_init__(self):
        # 初期化時にデフォルトのガチャを作成
        if not self.gacha_list:
            default_gacha = GachaSettings(
                messages=MessageSettings(
                    setup='**ガチャを回して運試し！**\n1日1回ガチャが回せるよ！',
                    daily='1日1回ガチャが回せます！\n下のボタンを押してガチャを実行してください。',
                    win='',
                    custom_messages={}
                ),
                media=MediaSettings(
                    setup_image='',
                    banner_gif=''
                )
            )
            self.gacha_list.append(default_gacha)

    def to_dict(self) -> dict:
        return {
            'enabled': self.enabled,
            'gacha_list': [gacha.to_dict() for gacha in self.gacha_list],
            'points': [asdict(p) for p in self.points] if self.points else [],
            'roles': [asdict(r) for r in self.roles] if self.roles else []
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GachaFeatureSettings':

        # print(f"[DEBUG] GachaFeatureSettings.from_dict input: {data}")

        # データがリストの場合の処理を追加
        if isinstance(data, list):
            gacha_list = []
            for gacha_data in data:
                try:
                    gacha_list.append(GachaSettings.from_dict(gacha_data))
                except Exception as e:
                    print(f"Error converting gacha settings from list: {e}")
                    continue
            return cls(
                enabled=True,
                gacha_list=gacha_list,
                points=[],
                roles=[]
            )
        gacha_list = []
        
        # 新形式のデータ構造の処理
        if 'gacha_list' in data:
            for gacha_data in data.get('gacha_list', []):
                try:
                    gacha_list.append(GachaSettings.from_dict(gacha_data))
                except Exception as e:
                    print(f"Error converting gacha settings: {e}")
                    continue
        # 古い形式のデータ構造の処理（後方互換性）
        elif 'messages' in data or 'media' in data or 'items' in data:
            try:
                legacy_gacha = GachaSettings(
                    messages=MessageSettings(**data.get('messages', {})) if data.get('messages') else None,
                    media=MediaSettings(**data.get('media', {})) if data.get('media') else None,
                    items=data.get('items', []),
                    roles=data.get('roles', [])
                )
                gacha_list.append(legacy_gacha)
            except Exception as e:
                print(f"Error converting legacy gacha settings: {e}")

        # print(f"[DEBUG] Converted gacha_list: {gacha_list}")


        # ポイントと報酬の設定を処理
        points = []
        if 'points' in data:
            for point_data in data.get('points', []):
                try:
                    points.append(PointDistribution(**point_data))
                except Exception as e:
                    print(f"Error converting point distribution: {e}")

        roles = []
        if 'roles' in data:
            for role_data in data.get('roles', []):
                try:
                    condition = RoleCondition(**role_data.get('condition', {}))
                    roles.append(RoleSettings(
                        role_id=role_data.get('role_id'),
                        condition=condition
                    ))
                except Exception as e:
                    print(f"Error converting role settings: {e}")

        return cls(
            enabled=data.get('enabled', True),
            gacha_list=gacha_list,
            points=points,
            roles=roles
        )

@dataclass
class BattleFeatureSettings:
    enabled: bool = True
    required_role_id: Optional[str] = None
    winner_role_id: Optional[str] = None
    points_enabled: bool = True
    points_per_kill: int = 100
    winner_points: int = 1000
    start_delay_minutes: int = 2
    unit_id: str = "1"  # デフォルトは "1" を設定

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
    error_messages: Dict[str, str] = field(default_factory=lambda: {
        "invalid_points": "無効なポイント値です。",
        "insufficient_points": "利用可能なポイントを超えています。",
        "invalid_wallet": "無効なウォレットアドレスです。",
        "invalid_email": "無効なメールアドレスです。",
        "save_error": "申請の保存に失敗しました。",
        "system_error": "申請処理中にエラーが発生しました。"
    })

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


class SubscriptionTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

    def __str__(self):
        return self.value

@dataclass
class SubscriptionFeatures:
    point_history: bool = False
    advanced_analytics: bool = False
    custom_branding: bool = False
    max_gacha_items: int = 50
    max_point_types: int = 1

    def to_dict(self) -> dict:
        return {
            'point_history': self.point_history,
            'advanced_analytics': self.advanced_analytics,
            'custom_branding': self.custom_branding,
            'max_gacha_items': self.max_gacha_items,
            'max_point_types': self.max_point_types
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SubscriptionFeatures':
        return cls(
            point_history=data.get('point_history', False),
            advanced_analytics=data.get('advanced_analytics', False),
            custom_branding=data.get('custom_branding', False),
            max_gacha_items=data.get('max_gacha_items', 50),
            max_point_types=data.get('max_point_types', 1)
        )

@dataclass
class SubscriptionSettings:
    tier: SubscriptionTier = SubscriptionTier.FREE
    features: SubscriptionFeatures = field(default_factory=SubscriptionFeatures)
    expires_at: Optional[str] = None  # ISOフォーマットの文字列として保存

    def to_dict(self) -> dict:
        return {
            'tier': self.tier.value,
            'features': self.features.to_dict(),
            'expires_at': self.expires_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SubscriptionSettings':
        if not data:
            return cls()
        
        return cls(
            tier=SubscriptionTier(data.get('tier', SubscriptionTier.FREE.value)),
            features=SubscriptionFeatures.from_dict(data.get('features', {})),
            expires_at=data.get('expires_at')
        )

@dataclass
class GlobalSettings:
    point_unit: str = "ポイント"
    timezone: str = "Asia/Tokyo"
    language: str = "ja"
    features_enabled: Dict[str, bool] = None
    multiple_points_enabled: bool = False
    point_units: List[PointUnit] = field(default_factory=lambda: [
        PointUnit(unit_id="1", name="ポイント")
    ])

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
    subscription_settings: SubscriptionSettings = field(default_factory=SubscriptionSettings)
    subscription_status: str = "free"  # デフォルト値を設定
    updated_at: str = None
    version: int = 1

    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
        if self.point_consumption_settings is None:  # 追加
            self.point_consumption_settings = PointConsumptionFeatureSettings()

    def to_dict(self) -> dict:
        """設定をDynamoDBに保存可能な形式に変換"""
        try:
            # デバッグ用のログを追加
            print(f"[DEBUG] gacha_settings type: {type(self.gacha_settings)}")
            print(f"[DEBUG] gacha_settings content: {self.gacha_settings}")
            return {
                'server_id': self.server_id,
                'global_settings': {
                    'point_unit': self.global_settings.point_unit,
                    'timezone': self.global_settings.timezone,
                    'language': self.global_settings.language,
                    'features_enabled': self.global_settings.features_enabled,
                    'multiple_points_enabled': self.global_settings.multiple_points_enabled,
                    'point_units': [
                        {'unit_id': unit.unit_id, 'name': unit.name}
                        for unit in self.global_settings.point_units
                    ]
                },
                'feature_settings': {
                    'gacha': self.gacha_settings.to_dict(),

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
                    },

                },
                'subscription_settings': self.subscription_settings.to_dict(),
                'updated_at': self.updated_at,
                'version': self.version
            }
        except Exception as e:
            print(f"[DEBUG] Error in to_dict: {e}")
            raise

    @classmethod
    def from_dict(cls, data: dict) -> 'ServerSettings':
        """DynamoDBから取得したデータをServerSettingsオブジェクトに変換"""
        if not data:
            return None

        global_settings_data = data.get('global_settings', {})
        global_settings = GlobalSettings(
            point_unit=global_settings_data.get('point_unit', 'ポイント'),
            timezone=global_settings_data.get('timezone', 'Asia/Tokyo'),
            language=global_settings_data.get('language', 'ja'),
            features_enabled=global_settings_data.get('features_enabled'),
            multiple_points_enabled=global_settings_data.get('multiple_points_enabled', False),
            point_units=[
                PointUnit(unit_id=unit['unit_id'], name=unit['name'])
                for unit in global_settings_data.get('point_units', [{'unit_id': '1', 'name': 'ポイント'}])
            ]
        )

        feature_settings = data.get('feature_settings', {})

        # ここを修正: feature_settings['gacha']の型をチェック
        gacha_data = feature_settings.get('gacha', {})
        if isinstance(gacha_data, list):
            # リストの場合、新しい形式のデータ構造に変換
            gacha_data = {
                'enabled': True,
                'gacha_list': gacha_data
            }
        
        gacha_settings = GachaFeatureSettings.from_dict(gacha_data)

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
        modal_settings = None
        if 'modal_settings' in point_consumption_data:
            modal_data = point_consumption_data['modal_settings']
            modal_settings = PointConsumptionModalSettings(
                title=modal_data.get('title', "ポイント消費申請"),
                fields=modal_data.get('fields', {
                    "points": True,
                    "wallet": False,
                    "email": False
                })
            )
        point_consumption_settings = PointConsumptionFeatureSettings(
            enabled=point_consumption_data.get('enabled', True),
            button_name=point_consumption_data.get('button_name', "ポイント消費"),
            channel_id=point_consumption_data.get('channel_id'),
            notification_channel_id=point_consumption_data.get('notification_channel_id'),
            mention_role_ids=point_consumption_data.get('mention_role_ids', []),
            use_thread=point_consumption_data.get('use_thread', False),
            completion_message_enabled=point_consumption_data.get('completion_message_enabled', True),
            required_points=point_consumption_data.get('required_points', 0),
            modal_settings=modal_settings,  # 明示的にmodal_settingsを渡す

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
            consumption_history_channel_id=point_consumption_data.get('consumption_history_channel_id'),
        )
        subscription_settings = SubscriptionSettings.from_dict(
                data.get('subscription_settings', {})
        )

        return cls(
            server_id=data['server_id'],
            global_settings=global_settings,
            gacha_settings=gacha_settings,
            battle_settings=battle_settings,
            fortune_settings=fortune_settings,
            point_consumption_settings=point_consumption_settings,  # 追加
            subscription_settings=subscription_settings,  # 追加
            updated_at=data.get('updated_at'),
            version=data.get('version', 1)
        )

