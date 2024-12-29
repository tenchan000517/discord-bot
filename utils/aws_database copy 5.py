import boto3
from datetime import datetime
import os
import pytz
from boto3.dynamodb.conditions import Key
from typing import Optional, Dict, List
import asyncio
import traceback
from decimal import Decimal

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

    async def get_server_settings(self, server_id: str) -> Optional[Dict]:
        """サーバー設定を非同期で取得"""
        try:
            # DynamoDB の非同期操作
            response = await asyncio.to_thread(
                self.settings_table.get_item,
                Key={'server_id': str(server_id)}
            )
            item = response.get('Item')

            if not item:
                # 初期設定を作成し保存
                default_settings = self._create_default_settings(server_id)
                await self.update_server_settings(server_id, default_settings)
                return default_settings

            return item
        except Exception as e:
            print(f"Error getting server settings: {e}")
            return None

    async def update_server_settings(self, server_id: str, settings: Dict) -> bool:
        """サーバー設定を非同期で更新"""
        try:
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
                        'banner_gif': 'https://nft-mint.xyz/gacha/gacha1.gif',
                        'gacha_animation_gif': 'https://nft-mint.xyz/gacha/gacha1.gif'
                    }
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
                    'gain_history_enabled': False,
                    'gain_history_channel_id': None,
                    'consumption_history_enabled': False,
                    'consumption_history_channel_id': None,
                    'logging_enabled': True,
                    'logging_channel_id': None,
                    'display_channel_id': None,
                    'logging_actions': ['click', 'complete', 'cancel']
                }            
            },
            'updated_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat(),
            'version': Decimal('1')
        }

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

    async def update_user_points(self, user_id: str, server_id: str, points: int) -> bool:
        """既存メソッドを新しい構造に対応させる"""
        try:
            return await self.update_feature_points(
                user_id, 
                server_id, 
                points, 
            )
        except Exception as e:
            print(f"Error in update_user_points: {e}")
            return False

    async def update_feature_points(self, user_id: str, server_id: str, points: int) -> bool:
        """ユーザーのポイントを更新"""
        try:
            from decimal import Decimal
            pk = self._create_pk(user_id, server_id)
            
            current_data = await self.get_user_data(user_id, server_id)
            if not current_data:
                current_data = {
                    'pk': pk,
                    'user_id': str(user_id),
                    'server_id': str(server_id),
                    'points': Decimal(str(points)),
                    'updated_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
                }
            else:
                current_data['points'] = Decimal(str(points))
                current_data['updated_at'] = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()

            await asyncio.to_thread(
                self.users_table.put_item,
                Item=current_data
            )
            return True
        except Exception as e:
            print(f"Error updating points: {e}")
            print(traceback.format_exc())
            return False
        
    async def get_user_points(self, user_id: str, server_id: str) -> int:
        """ユーザーの合計ポイントを取得"""
        try:
            data = await self.get_user_data(user_id, server_id)
            if not data:
                return 0
            return int(data.get('points', 0))
        except Exception as e:
            print(f"Error getting user points: {e}")
            return 0

    @staticmethod
    def _create_pk(user_id: str, server_id: str) -> str:
        """プライマリキーを生成"""
        return f"USER#{user_id}#SERVER#{server_id}"

    async def get_user_data(self, user_id: str, server_id: str) -> Optional[Dict]:
        """ユーザーのデータを非同期で取得"""
        try:
            pk = self._create_pk(user_id, server_id)
            response = await asyncio.to_thread(
                self.users_table.get_item,
                Key={'pk': pk}
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error getting user data: {e}")
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

    async def create_consumption_request(
        self,
        server_id: str,
        user_id: str,
        points: int,
        thread_id: Optional[str] = None
    ) -> Optional[Dict]:
        """消費リクエストを作成"""
        try:
            timestamp = datetime.now(pytz.UTC).isoformat()
            item = {
                'server_id': str(server_id),
                'user_id': str(user_id),
                'timestamp': timestamp,
                'points': points,
                'consumption_status': 'pending',
                'created_at': timestamp
            }

            if thread_id:
                item['thread_id'] = thread_id

            await asyncio.to_thread(
                self.point_consumption_history_table.put_item,
                Item=item
            )

            return item
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
            update_expression = "SET consumption_status = :status, admin_id = :admin, updated_at = :time"
            expression_values = {
                ':status': status,
                ':admin': admin_id,
                ':time': datetime.now(pytz.UTC).isoformat()
            }

            if reason:
                update_expression += ", status_reason = :reason"
                expression_values[':reason'] = reason

            await asyncio.to_thread(
                self.point_consumption_history_table.update_item,
                Key={
                    'server_id': str(server_id),
                    'timestamp': timestamp
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )

            return True
        except Exception as e:
            print(f"Error updating consumption status: {e}")
            return False
        
    # utils/aws_database.py に追加

    async def register_server(self, server_id: str):
        """サーバーIDをserver_settingsテーブルに登録"""
        try:
            # 既存の設定を確認
            response = await asyncio.to_thread(
                self.settings_table.get_item,
                Key={'server_id': str(server_id)}
            )
            
            # 設定が存在しない場合のみ、デフォルト設定を作成
            if 'Item' not in response:
                default_settings = self._create_default_settings(server_id)
                await asyncio.to_thread(
                    self.settings_table.put_item,
                    Item=default_settings
                )
            return True
        except Exception as e:
            print(f"Error registering server {server_id}: {e}")
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