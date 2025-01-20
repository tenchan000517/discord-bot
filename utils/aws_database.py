import boto3
from datetime import datetime
import os
import pytz
from boto3.dynamodb.conditions import Key
from typing import Optional, Dict, List, Union
import asyncio
import traceback
from decimal import Decimal
import uuid

class AWSDatabase:
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.users_table = self.dynamodb.Table('discord_users')
        self.settings_table = self.dynamodb.Table('server_settings')
        # self.history_table = self.dynamodb.Table('gacha_history')

        self.automation_rules_table = self.dynamodb.Table('automation_rules')
        # self.automation_history_table = self.dynamodb.Table('automation_history')

        self.point_consumption_history_table = self.dynamodb.Table('point_consumption_history')

    async def get_server_settings(self, server_id: str) -> Optional[Dict]:
        """
        DynamoDBからサーバー設定を取得する
        
        Args:
            server_id (str): サーバーID
            
        Returns:
            Optional[Dict]: 設定データ。存在しない場合はNone
        """
        try:
            response = await asyncio.to_thread(
                self.settings_table.get_item,
                Key={'server_id': str(server_id)}
            )
            return response.get('Item')  # 存在しない場合はNoneを返す
            
        except Exception as e:
            print(f"Error getting server settings: {e}")
            return None
        
    # ３番目に呼び出される serversettings_managerのcreate_default_settingsから呼び出される
    async def update_server_settings(self, server_id: str, settings: Dict) -> bool:
        """サーバー設定を非同期で更新"""
        try:
            # print(f"[DEBUG] Received settings in update_server_settings: {settings}")
            # print(f"[DEBUG] Type of settings in update_server_settings: {type(settings)}")

            # 必要なフィールドの補完
            settings['server_id'] = str(server_id)
            settings['updated_at'] = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
            if 'version' not in settings:
                settings['version'] = 1

            # DynamoDB の非同期操作
            await asyncio.to_thread(
                self.settings_table.put_item,
                Item=settings
            )
            return True
        except Exception as e:
            print(f"Error updating server settings: {e}")
            return False

    async def update_feature_settings(self, server_id: str, feature: str, settings: Dict) -> bool:
        try:
            current_settings = await self.get_server_settings(server_id)
            if not current_settings:
                return False

            # feature_settings が存在しない場合は作成
            if 'feature_settings' not in current_settings:
                current_settings['feature_settings'] = {}

            # ガチャ設定の場合、デフォルト値とマージ
            if feature == 'gacha':
                default_gacha = self._create_default_settings(server_id)['feature_settings']['gacha']
                merged_settings = {
                    **default_gacha,  # デフォルト値をベースに
                    **settings,       # 新しい設定で上書き
                    'messages': settings.get('messages', default_gacha['messages']),
                    'media': settings.get('media', default_gacha['media'])
                }
                current_settings['feature_settings'][feature] = merged_settings
            else:
                current_settings['feature_settings'][feature] = settings

            return await self.update_server_settings(server_id, current_settings)
        except Exception as e:
            print(f"Error updating feature settings: {e}")
            return False

    def _create_default_settings(self, server_id: str) -> Dict:
        """デフォルト設定を生成（同期処理で実行）"""
        return {
            'server_id': str(server_id),
            'global_settings': {
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
            'feature_settings': {
                'gacha': {
                    'enabled': True,
                    'gacha_list': [{ 
                        'gacha_id': str(uuid.uuid4()), 
                        'name': "デフォルトガチャ",
                        'enabled': True,
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
                            'win': None,
                            'tweet_message': None
                        },
                        'use_daily_panel': False,
                        'media': {
                            'setup_image': 'https://nft-mint.xyz/gacha/gacha1.png',
                            'banner_gif': 'https://nft-mint.xyz/gacha/gacha1.png',
                            'gacha_animation_gif': 'https://nft-mint.xyz/gacha/gacha1.gif'
                        }
                    }]
                },
                'battle': {
                    'enabled': True,
                    'required_role_id': None,
                    'winner_role_id': None,
                    'points_enabled': True,
                    'points_per_kill': Decimal('10'),
                    'winner_points': Decimal('100'),
                    'start_delay_minutes': Decimal('2')
                },
                'fortune': {'enabled': True, 'custom_messages': {}},
                'rewards': {
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
                    'logging_enabled': True,
                    'logging_channel_id': None,
                    'logging_actions': ['click', 'complete', 'cancel'],
                    'gain_history_enabled': False,
                    'gain_history_channel_id': None,
                    'consumption_history_enabled': False,
                    'consumption_history_channel_id': None,
                    'display_channel_id': None,
                    # モーダル設定を別オブジェクトとして定義
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
            'updated_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat(),
            'version': Decimal('1')
        }

    async def get_gacha_settings(self, server_id: str, gacha_id: Optional[str] = None) -> Union[Dict, List[Dict]]:
        """ガチャ設定を取得。gacha_idが指定されない場合は全てのガチャ設定を返す"""
        try:
            settings = await self.get_server_settings(server_id)
            if not settings or 'feature_settings' not in settings or 'gacha' not in settings['feature_settings']:
                return [] if gacha_id is None else None

            gacha_settings = settings['feature_settings']['gacha']
            
            # 単一のガチャ設定の場合は配列に変換
            if not isinstance(gacha_settings, list):
                gacha_settings = [gacha_settings]

            if gacha_id:
                # 特定のガチャ設定を返す
                for gacha in gacha_settings:
                    if gacha.get('gacha_id') == gacha_id:
                        return gacha
                return None
            
            return gacha_settings
        except Exception as e:
            print(f"Error getting gacha settings: {e}")
            return [] if gacha_id is None else None

    async def add_gacha_settings(self, server_id: str, new_gacha_settings: Dict) -> bool:
        """新しいガチャ設定を追加"""
        try:
            settings = await self.get_server_settings(server_id)
            if not settings:
                return False

            if 'feature_settings' not in settings:
                settings['feature_settings'] = {}
            
            if 'gacha' not in settings['feature_settings']:
                settings['feature_settings']['gacha'] = []
            elif not isinstance(settings['feature_settings']['gacha'], list):
                # 既存の単一ガチャ設定を配列に変換
                settings['feature_settings']['gacha'] = [settings['feature_settings']['gacha']]

            # チャンネルの重複チェック
            for gacha in settings['feature_settings']['gacha']:
                if gacha.get('channel_id') == new_gacha_settings.get('channel_id'):
                    return False

            # 新しいガチャ設定を追加
            settings['feature_settings']['gacha'].append(new_gacha_settings)
            
            return await self.update_server_settings(server_id, settings)
        except Exception as e:
            print(f"Error adding gacha settings: {e}")
            return False

    async def update_gacha_settings(self, server_id: str, gacha_id: str, updated_settings: Dict) -> bool:
        """特定のガチャ設定を更新"""
        try:
            settings = await self.get_server_settings(server_id)
            if not settings or 'feature_settings' not in settings or 'gacha' not in settings['feature_settings']:
                return False

            gacha_settings = settings['feature_settings']['gacha']
            if not isinstance(gacha_settings, list):
                gacha_settings = [gacha_settings]

            # ガチャ設定の更新
            found = False
            for i, gacha in enumerate(gacha_settings):
                if gacha.get('gacha_id') == gacha_id:
                    # チャンネルIDが変更される場合は重複チェック
                    if 'channel_id' in updated_settings:
                        for other_gacha in gacha_settings:
                            if (other_gacha.get('gacha_id') != gacha_id and 
                                other_gacha.get('channel_id') == updated_settings['channel_id']):
                                return False
                    
                    gacha_settings[i] = {**gacha, **updated_settings}
                    found = True
                    break

            if not found:
                return False

            settings['feature_settings']['gacha'] = gacha_settings
            return await self.update_server_settings(server_id, settings)
        except Exception as e:
            print(f"Error updating gacha settings: {e}")
            return False

    async def delete_gacha_settings(self, server_id: str, gacha_id: str) -> bool:
        """ガチャ設定を削除"""
        try:
            settings = await self.get_server_settings(server_id)
            if not settings or 'feature_settings' not in settings or 'gacha' not in settings['feature_settings']:
                return False

            gacha_settings = settings['feature_settings']['gacha']
            if not isinstance(gacha_settings, list):
                gacha_settings = [gacha_settings]

            # ガチャ設定の削除
            settings['feature_settings']['gacha'] = [
                gacha for gacha in gacha_settings 
                if gacha.get('gacha_id') != gacha_id
            ]

            return await self.update_server_settings(server_id, settings)
        except Exception as e:
            print(f"Error deleting gacha settings: {e}")
            return False

    async def get_gacha_by_channel(self, server_id: str, channel_id: str) -> Optional[Dict]:
        """チャンネルIDからガチャ設定を取得"""
        try:
            gacha_settings = await self.get_gacha_settings(server_id)
            if not gacha_settings:
                return None

            for gacha in gacha_settings:
                if gacha.get('channel_id') == channel_id:
                    return gacha
            return None
        except Exception as e:
            print(f"Error getting gacha by channel: {e}")
            return None

    async def get_server_user_rankings(self, server_id: str) -> List[Dict]:
        """サーバー内のユーザーランキングを取得"""
        try:
            # テーブル全体をスキャン
            response = await asyncio.to_thread(
                self.users_table.scan
            )
            
            # サーバーに関連するデータをフィルタリング
            server_rankings = []
            for item in response.get('Items', []):
                pk = item.get('pk', '')
                if f'SERVER#{server_id}' in pk:
                    user_id = pk.split('#')[1]  # USER#{user_id}#SERVER#{server_id}
                    points = int(float(item.get('points', 0)))  # Decimal -> float -> int
                    server_rankings.append({
                        'user_id': user_id,
                        'points': points
                    })
            
            # ポイントで降順ソート
            server_rankings.sort(key=lambda x: x['points'], reverse=True)
            print(f"[DEBUG] サーバー {server_id} のユーザー数: {len(server_rankings)}")
            return server_rankings
                
        except Exception as e:
            print(f"Error getting server rankings: {str(e)}")
            print(traceback.format_exc())
            return []

    async def get_all_user_rankings(self) -> List[Dict]:
        """全サーバーのユーザーランキングを取得"""
        try:
            # テーブル全体をスキャン
            response = await asyncio.to_thread(
                self.users_table.scan
            )
            
            # ユーザーごとの合計ポイントを集計
            user_points = {}
            for item in response.get('Items', []):
                pk = item.get('pk', '')
                if 'USER#' in pk:
                    user_id = pk.split('#')[1]
                    points = int(float(item.get('points', 0)))  # Decimal -> float -> int
                    
                    if user_id in user_points:
                        user_points[user_id] += points
                    else:
                        user_points[user_id] = points
            
            # ランキングリストを作成
            rankings = [
                {'user_id': user_id, 'points': points}
                for user_id, points in user_points.items()
            ]
            
            # ポイントで降順ソート
            rankings.sort(key=lambda x: x['points'], reverse=True)
            print(f"[DEBUG] 全サーバーの総ユーザー数: {len(rankings)}")
            return rankings
                
        except Exception as e:
            print(f"Error getting all rankings: {str(e)}")
            print(traceback.format_exc())
            return []

    async def update_user_points(self, user_id: str, server_id: str, points: int, unit_id: str = "1") -> bool:
        """既存メソッドを新しい構造に対応させる"""
        try:
            return await self.update_feature_points(
                user_id, 
                server_id, 
                points,
                unit_id
            )
        except Exception as e:
            print(f"Error in update_user_points: {e}")
            return False

    async def update_feature_points(self, user_id: str, server_id: str, points: int, unit_id: str = "1") -> bool:
        """
        ユーザーのポイントを更新する

        Args:
            user_id (str): ユーザーのDiscord ID
            server_id (str): サーバーのDiscord ID
            points (int): 更新後の最終的なポイント値
            unit_id (str, optional): ポイントユニットのID. デフォルトは "1"

        Returns:
            bool: 更新が成功したかどうか

        Note:
            - pointsパラメータには更新後の最終的なポイント値を渡すこと
            - 例:現在のポイントが100で、50ポイント消費する場合は、points=50を渡す
            - 新規ユーザーの場合は新しいレコードを作成
            - 既存ユーザーの場合は指定されたポイント値で更新
        """
        try:
            # パーティションキーを生成
            pk = self._create_pk(user_id, server_id, unit_id)
            
            # 現在のユーザーデータを取得
            current_data = await self.get_user_data(user_id, server_id, unit_id)
            
            if not current_data:
                # 新規ユーザーの場合、新しいレコードを作成
                current_data = {
                    'pk': pk,
                    'user_id': str(user_id),
                    'server_id': str(server_id),
                    'unit_id': unit_id,
                    'points': Decimal(str(points)),
                    'created_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat(),
                    'updated_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
                }
            else:
                # 既存ユーザーの場合、ポイントと更新日時を更新
                current_data['points'] = Decimal(str(points))
                current_data['updated_at'] = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()

            # DynamoDBにデータを保存
            await asyncio.to_thread(
                self.users_table.put_item,
                Item=current_data
            )
            
            print(f"[DEBUG] Successfully updated points for user {user_id} to {points}")
            return True
            
        except Exception as e:
            print(f"Error updating points: {e}")
            print(traceback.format_exc())
            return False
        
    async def get_user_points(self, user_id: str, server_id: str, unit_id: str = "1") -> int:
        """ユーザーの合計ポイントを取得"""
        try:
            data = await self.get_user_data(user_id, server_id, unit_id)
            if not data:
                return 0
            return int(data.get('points', 0))
        except Exception as e:
            print(f"Error getting user points: {e}")
            return 0

    def _create_pk(self, user_id: str, server_id: str, unit_id: str = "1") -> str:
        """
        ユーザーデータ用のプライマリキーを生成する

        Args:
            user_id (str): ユーザーのDiscord ID
            server_id (str): サーバーのDiscord ID
            unit_id (str, optional): ポイントユニットのID. デフォルトは "1"

        Returns:
            str: 生成されたプライマリキー (形式: USER#{user_id}#SERVER#{server_id}#UNIT#{unit_id})

        Raises:
            ValueError: パラメータが無効な場合（空文字列や不適切な型）
        """
        try:
            # パラメータの検証
            if not all(isinstance(x, str) for x in [user_id, server_id, unit_id]):
                raise ValueError("All parameters must be strings")
            
            if not all(x.strip() for x in [user_id, server_id, unit_id]):
                raise ValueError("All parameters must be non-empty strings")

            # プライマリキーの生成
            pk = f"USER#{user_id}#SERVER#{server_id}#UNIT#{unit_id}"
            print(f"[DEBUG] Generated PK: {pk}")
            return pk

        except Exception as e:
            print(f"[ERROR] Error in _create_pk: {e}")
            raise

    async def get_user_data(self, user_id: str, server_id: str, unit_id: str = "1") -> Optional[Dict]:
        """
        指定されたユーザー、サーバー、ユニットIDに対応するデータを取得する

        Args:
            user_id (str): ユーザーのDiscord ID
            server_id (str): サーバーのDiscord ID
            unit_id (str, optional): ポイントユニットのID. デフォルトは "1"

        Returns:
            Optional[Dict]: ユーザーデータを含む辞書。データが存在しない場合はNone

        Raises:
            Exception: データベースアクセスに失敗した場合
        """
        try:
            print(f"[DEBUG] Getting user data for:")
            print(f"  user_id: {user_id}")
            print(f"  server_id: {server_id}")
            print(f"  unit_id: {unit_id}")

            # プライマリキーの生成
            pk = self._create_pk(user_id, server_id, unit_id)
            print(f"[DEBUG] Using PK for query: {pk}")
            print(f"[DEBUG] PK exact length: {len(pk)}")
            print(f"[DEBUG] PK character codes: {[ord(c) for c in pk]}")  # 不可視文字のチェック

            # DynamoDBからデータ取得
            response = await asyncio.to_thread(
                self.users_table.get_item,
                Key={'pk': pk}
            )
            print(f"[DEBUG] DynamoDB response: {response}")

            return response.get('Item')

        except Exception as e:
            print(f"[ERROR] Error in get_user_data: {e}")
            print(traceback.format_exc())
            return None

        
    async def get_automation_rules(self, server_id: str) -> List[Dict]:
        """サーバーのオートメーションルールを非同期で取得"""
        try:
            response = await asyncio.to_thread(
                self.automation_rules_table.query,
                KeyConditionExpression=Key('server_id').eq(str(server_id))
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting automation rules: {e}")
            return []

    async def save_automation_rule(self, rule_data: dict) -> bool:
        """オートメーションルールを非同期で保存"""
        try:
            await asyncio.to_thread(
                self.automation_rules_table.put_item,
                Item=rule_data
            )
            return True
        except Exception as e:
            print(f"Error saving automation rule: {e}")
            return False

    async def delete_automation_rule(self, server_id: str, rule_id: str) -> bool:
        """オートメーションルールを非同期で削除"""
        try:
            await asyncio.to_thread(
                self.automation_rules_table.delete_item,
                Key={
                    'server_id': str(server_id),
                    'rule_id': str(rule_id)
                }
            )
            return True
        except Exception as e:
            print(f"Error deleting automation rule: {e}")
            return False

    # これをログ通知設定で特定のチャンネルに通知する設定を後々作る
    # async def save_automation_history(self, history_data: dict) -> bool:
    #     """オートメーション実行履歴を非同期で保存"""
    #     try:
    #         # タイムスタンプをソートキーとして使用
    #         history_data['timestamp'] = datetime.now(pytz.UTC).isoformat()
            
    #         await asyncio.to_thread(
    #             self.automation_history_table.put_item,
    #             Item=history_data
    #         )
    #         return True
    #     except Exception as e:
    #         print(f"Error saving automation history: {e}")
    #         return False

    # async def get_automation_history(self, server_id: str, limit: int = 100) -> List[Dict]:
    #     """サーバーのオートメーション実行履歴を非同期で取得"""
    #     try:
    #         response = await asyncio.to_thread(
    #             self.automation_history_table.query,
    #             KeyConditionExpression=Key('server_id').eq(str(server_id)),
    #             Limit=limit,
    #             ScanIndexForward=False  # 最新のものから取得
    #         )
    #         return response.get('Items', [])
    #     except Exception as e:
    #         print(f"Error getting automation history: {e}")
    #         return []

    async def get_automation_rule(self, server_id: str, rule_id: str) -> Optional[Dict]:
        """特定のオートメーションルールを非同期で取得"""
        try:
            response = await asyncio.to_thread(
                self.automation_rules_table.get_item,
                Key={
                    'server_id': str(server_id),
                    'rule_id': str(rule_id)
                }
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error getting automation rule: {e}")
            return None

    async def save_reward(self, reward_data: dict) -> bool:
        """報酬データを保存"""
        try:
            await asyncio.to_thread(
                self.reward_claims_table.put_item,
                Item=reward_data
            )
            return True
        except Exception as e:
            print(f"Error saving reward: {e}")
            return False

    async def get_user_rewards(
        self,
        user_id: str,
        server_id: str,
        status: Optional[str] = None
    ) -> List[Dict]:
        """ユーザーの報酬履歴を取得"""
        try:
            # クエリ条件の構築
            key_condition = Key('user_id').eq(str(user_id))
            filter_expression = None

            if status:
                filter_expression = Attr('status').eq(status)
                if server_id:
                    filter_expression = filter_expression & Attr('server_id').eq(str(server_id))
            elif server_id:
                filter_expression = Attr('server_id').eq(str(server_id))

            # クエリの実行
            kwargs = {
                'KeyConditionExpression': key_condition,
                'ScanIndexForward': False  # 新しい順
            }
            if filter_expression:
                kwargs['FilterExpression'] = filter_expression

            response = await asyncio.to_thread(
                self.reward_claims_table.query,
                **kwargs
            )
            return response.get('Items', [])

        except Exception as e:
            print(f"Error getting user rewards: {e}")
            return []
        
    async def get_rewards_by_status(
        self,
        status: str,
        server_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """ステータスごとの報酬履歴を取得"""
        try:
            kwargs = {
                'IndexName': 'StatusIndex',
                'KeyConditionExpression': Key('status').eq(status),
                'Limit': limit,
                'ScanIndexForward': False
            }

            if server_id:
                kwargs['FilterExpression'] = Attr('server_id').eq(str(server_id))

            response = await asyncio.to_thread(
                self.reward_claims_table.query,
                **kwargs
            )
            return response.get('Items', [])

        except Exception as e:
            print(f"Error getting rewards by status: {e}")
            return []
        
    async def save_consumption_history(self, history_data: dict) -> bool:
        """消費履歴をデータベースに保存"""
        try:
            timestamp = datetime.now(pytz.UTC).isoformat()
            item = {
                'server_id': history_data['server_id'],
                'timestamp': timestamp,
                'user_id': history_data['user_id'],
                'points': history_data['points'],
                'wallet_address': history_data.get('wallet_address'),
                'email': history_data.get('email'),
                'status': history_data.get('status', 'pending'),
                'created_at': timestamp,
                'updated_at': timestamp,
                'thread_id': history_data.get('thread_id'),
                'unit_id': history_data.get('unit_id')  # unit_idを追加
            }
            await asyncio.to_thread(
                self.point_consumption_history_table.put_item,
                Item=item
            )
            return True
        except Exception as e:
            print(f"Error saving consumption history: {e}")
            return False

    async def get_user_consumption_history(
        self,
        server_id: str,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """ユーザーの消費履歴を取得"""
        try:
            response = await asyncio.to_thread(
                self.point_consumption_history_table.query,
                IndexName='UserIndex',
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id},
                ScanIndexForward=False,
                Limit=limit
            )
            items = response.get('Items', [])
            # 各アイテムにunit_idが存在しない場合はデフォルト値を設定
            for item in items:
                item['unit_id'] = item.get('unit_id', '1')
            return items
        except Exception as e:
            print(f"Error getting user consumption history: {e}")
            return []

    # async def get_consumption_history(
    #     self,
    #     server_id: str,
    #     limit: int = 100,
    #     user_id: Optional[str] = None,
    #     status: Optional[str] = None
    # ) -> List[Dict]:
    #     """消費履歴を取得"""
    #     try:
    #         if user_id:
    #             # 特定ユーザーの履歴を取得
    #             command = {
    #                 'TableName': 'point_consumption_history',
    #                 'IndexName': 'UserIndex',
    #                 'KeyConditionExpression': 'user_id = :uid',
    #                 'ExpressionAttributeValues': {':uid': user_id},
    #                 'ScanIndexForward': False,  # 新しい順
    #                 'Limit': limit
    #             }
    #         else:
    #             # サーバー全体の履歴を取得
    #             command = {
    #                 'TableName': 'point_consumption_history',
    #                 'KeyConditionExpression': 'server_id = :sid',
    #                 'ExpressionAttributeValues': {':sid': str(server_id)},
    #                 'ScanIndexForward': False,
    #                 'Limit': limit
    #             }

    #         # ステータスフィルター追加
    #         if status:
    #             command['FilterExpression'] = 'consumption_status = :status'
    #             command['ExpressionAttributeValues'][':status'] = status

    #         result = await asyncio.to_thread(
    #             self.point_consumption_history_table.query,
    #             **command
    #         )

    #         return result.get('Items', [])

    #     except Exception as e:
    #         print(f"Error getting consumption history: {e}")
    #         return []

    async def update_point_consumption_settings(self, server_id: str, settings: dict) -> bool:
        """ポイント消費機能の設定を更新"""
        try:
            # 現在のサーバー設定を取得
            current_settings = await self.get_server_settings(server_id)
            if not current_settings:
                return False

            # feature_settings が存在しない場合は作成
            if 'feature_settings' not in current_settings:
                current_settings['feature_settings'] = {}

            # 設定を更新
            current_settings['feature_settings']['point_consumption'] = settings

            # データベースに保存
            return await self.update_server_settings(server_id, current_settings)

        except Exception as e:
            print(f"Error updating point consumption settings: {e}")
            return False

    async def get_point_consumption_settings(self, server_id: str) -> dict:
        """ポイント消費機能の設定を取得"""
        try:
            settings = await self.get_server_settings(server_id)
            if not settings or 'feature_settings' not in settings:
                return self._create_default_settings(server_id)['feature_settings']['point_consumption']

            return settings['feature_settings'].get('point_consumption', 
                self._create_default_settings(server_id)['feature_settings']['point_consumption'])

        except Exception as e:
            print(f"Error getting point consumption settings: {e}")
            return self._create_default_settings(server_id)['feature_settings']['point_consumption']

    async def create_consumption_request(
            self,
            guild_id: str,
            user_id: str,
            points: int,
            thread_id: str = None,
            wallet_address: str = None,
            email: str = None
        ) -> dict:
            try:
                timestamp = datetime.now(pytz.UTC).isoformat()
                request_data = {
                    'server_id': str(guild_id),
                    'user_id': str(user_id),
                    'points': points,
                    'timestamp': timestamp,
                    'thread_id': thread_id,
                    'status': 'pending',
                    'wallet_address': wallet_address,
                    'email': email,
                    'created_at': timestamp
                }
                
                # データベースに保存
                success = await self.bot.db.save_consumption_history(request_data)
                if not success:
                    raise Exception("Failed to save consumption request")

                return request_data

            except Exception as e:
                print(f"Error creating consumption request: {e}")
                return None

    async def update_consumption_status(
        self,
        server_id: str,
        timestamp: str,
        status: str,
        admin_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """消費リクエストのステータスを更新"""
        try:
            update_expression = "SET #s = :status, admin_id = :admin_id, updated_at = :time"
            expression_names = {
                '#s': 'status'  # status は予約語なので # を使用
            }
            expression_values = {
                ':status': status,
                ':admin_id': admin_id,
                ':time': datetime.now(pytz.UTC).isoformat()
            }

            if reason:
                update_expression += ", status_reason = :reason"
                expression_values[':reason'] = reason

            print(f"[DEBUG] Updating DynamoDB with expression: {update_expression}")
            print(f"[DEBUG] Expression names: {expression_names}")
            print(f"[DEBUG] Expression values: {expression_values}")

            await asyncio.to_thread(
                self.point_consumption_history_table.update_item,
                Key={
                    'server_id': str(server_id),
                    'timestamp': timestamp
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values
            )

            # 更新後の値を確認するためのログ
            result = await asyncio.to_thread(
                self.point_consumption_history_table.get_item,
                Key={
                    'server_id': str(server_id),
                    'timestamp': timestamp
                }
            )
            print(f"[DEBUG] Updated item: {result.get('Item')}")


            return True
        except Exception as e:
            print(f"Error updating consumption status: {e}")
            print(traceback.format_exc())  # スタックトレースを出力
            return False
        
    async def get_consumption_request(self, server_id: str, timestamp: str) -> Optional[Dict]:
        """
        消費リクエストの状態を取得
        :param server_id: サーバーID
        :param timestamp: リクエストのタイムスタンプ
        :return: リクエストデータ（存在しない場合は None）
        """
        try:
            response = await asyncio.to_thread(
                self.point_consumption_history_table.get_item,
                Key={
                    'server_id': str(server_id),
                    'timestamp': timestamp
                }
            )
            item = response.get('Item')
            if item:
                # unit_idがない場合はデフォルト値を設定
                item['unit_id'] = item.get('unit_id', '1')
            return item
        except Exception as e:
            print(f"Error fetching consumption request: {e}")
            return None

    # bot招待後一番最初に仕事をする→settings_managerのcreate_default_settingsへ
    async def register_server(self, server_id: str):
        """サーバーがDB上に存在するかどうかをチェックする関数"""
        try:
            # 既存の設定を確認
            response = await asyncio.to_thread(
                self.settings_table.get_item,
                Key={'server_id': str(server_id)}
            )
            
            # 存在チェックの結果を返す
            exists = 'Item' in response
            return exists

        except Exception as e:
            print(f"Error checking server {server_id}: {e}")
            raise

    async def remove_server(self, server_id: str):
        """サーバーIDをserver_settingsテーブルから削除"""
        try:
            await asyncio.to_thread(
                self.settings_table.delete_item,
                Key={'server_id': str(server_id)}
            )
            return True
        except Exception as e:
            print(f"Error removing server {server_id}: {e}")
            raise

    async def register_existing_servers(self, guilds):
        """既存のサーバーを一括登録"""
        for guild in guilds:
            try:
                await self.register_server(str(guild.id))
                print(f"Registered existing server: {guild.name} (ID: {guild.id})")
            except Exception as e:
                print(f"Error registering existing server {guild.id}: {e}")

    # インスタンス初期化時にテーブル参照を追加
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        # 既存のテーブル参照
        self.users_table = self.dynamodb.Table('discord_users')
        self.settings_table = self.dynamodb.Table('server_settings')
        self.history_table = self.dynamodb.Table('gacha_history')
        self.automation_rules_table = self.dynamodb.Table('automation_rules')
        # 新規テーブル参照を追加
        self.point_consumption_history_table = self.dynamodb.Table('point_consumption_history')