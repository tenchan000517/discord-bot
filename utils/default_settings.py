from datetime import datetime
import pytz
from decimal import Decimal
import uuid
from typing import Dict
from models.server_settings import FeatureType

def create_default_settings(server_id: str) -> Dict:
    """デフォルトのサーバー設定を辞書形式で生成"""
    return {
        'server_id': str(server_id),
        'global_settings': {
            'point_unit': 'ポイント',
            'timezone': 'Asia/Tokyo',
            'language': 'ja',
            'features_enabled': {
                FeatureType.GACHA.value: True,
                FeatureType.BATTLE.value: True,
                FeatureType.FORTUNE.value: True,
                FeatureType.POINT_CONSUMPTION.value: True,
            },
            'multiple_points_enabled': False,
            'point_units': [
                {
                    'unit_id': "1",
                    'name': "ポイント"
                }
            ]
        },
        'feature_settings': {
            'gacha': {
                'enabled': True,
                'gacha_list': [{ 
                    'gacha_id': str(uuid.uuid4()),
                    'name': "デフォルトガチャ",
                    'channel_id': None,
                    'enabled': True,
                    'roles': [],
                    'use_daily_panel': True,
                    'point_unit_id': "1",
                    'items': [
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
                    ],
                    'messages': {
                        'setup': '**ガチャを回して運試し！**\n1日1回ガチャが回せるよ！',
                        'daily': '1日1回ガチャが回せます！\n下のボタンを押してガチャを実行してください。',
                        'win': '',
                        'custom_messages': {},
                        'tweet_message': None,
                        'panel_title': 'デイリーガチャ',
                        'button_labels': {
                            'gacha': 'ガチャを回す！',
                            'share': 'ガチャ結果をXに投稿',
                            'points': 'ポイントを確認'
                        }
                    },
                    'media': {
                        'setup_image': 'https://nft-mint.xyz/gacha/gacha1.png',
                        'banner_gif': 'https://nft-mint.xyz/gacha/gacha1.png',
                        'gacha_animation_gif': 'https://nft-mint.xyz/gacha/gacha1.gif'
                    }
                }],
                'points': [],
                'roles': []
            },
            'battle': {
                'enabled': True,
                'required_role_id': None,
                'winner_role_id': None,
                'points_enabled': True,
                'points_per_kill': Decimal('100'),
                'winner_points': Decimal('1000'),
                'start_delay_minutes': Decimal('2'),
                'unit_id': "1"  # デフォルトのunit_idを追加    
            },
            'fortune': {
                'enabled': True,
                'custom_messages': {}
            },
            'point_consumption': {
                'enabled': True,
                'button_name': "ポイント消費",
                'channel_id': None,
                'notification_channel_id': None,
                'mention_role_ids': [],
                'use_thread': False,
                'completion_message_enabled': True,
                'required_points': Decimal('0'),
                'panel_message': "クリックしてポイントの消費申請をしてください",
                'panel_title': "ポイント消費",
                'thread_welcome_message': "{user}こちらからポイント消費申請を行ってください\nあなたの申請可能ポイントは{points}{unit}です",
                'notification_message': "{user}が{points}{unit}の申請をしました",
                'completion_message': "{user}が{points}{unit}を消費しました。管理者: {admin}",
                'approval_roles': [],
                'admin_override': True,
                'history_channel_id': None,
                'history_enabled': False,
                'history_format': "{user}が{points}{unit}を消費しました\nステータス: {status}",
                'logging_enabled': False,
                'logging_channel_id': None,
                'logging_actions': [],
                'gain_history_enabled': False,
                'gain_history_channel_id': None,
                'consumption_history_enabled': False,
                'consumption_history_channel_id': None,
                'modal_settings': {
                    'title': "ポイント消費申請",
                    'fields': {
                        "points": True,
                        "wallet": False,
                        "email": False
                    },
                    'field_labels': {
                        "points": "消費ポイント",
                        "wallet": "ウォレットアドレス",
                        "email": "メールアドレス"
                    },
                    'field_placeholders': {
                        "points": "消費するポイント数を入力",
                        "wallet": "0x...",
                        "email": "example@example.com"
                    },
                    'validation': {
                        "points": {"min": 0, "max": None},
                        "wallet": {"pattern": "^0x[a-fA-F0-9]{40}$"},
                        "email": {"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"}
                    },
                    'success_message': "申請を送信しました。"
                }
            }
        },
        'subscription_settings': {
            'tier': 'free',
            'features': {
                'point_history': False,
                'advanced_analytics': False,
                'custom_branding': False,
                'max_gacha_items': 50,
                'max_point_types': 1
            },
            'expires_at': None
        },
        'subscription_status': 'free',  # 追加項目: サブスクリプションのステータス
        'updated_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat(),
        'version': Decimal('1')
    }