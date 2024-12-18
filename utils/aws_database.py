import boto3
from datetime import datetime
import os
import pytz
from boto3.dynamodb.conditions import Key
from typing import Optional, Dict, List
import asyncio

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
        self.history_table = self.dynamodb.Table('gacha_history')

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
                    'fortune': True
                }
            },
            'feature_settings': {
                'gacha': {
                    'enabled': True,
                    'items': [
                        {'name': 'SSRアイテム', 'weight': 5, 'points': 100, 'image_url': ''},
                        {'name': 'SRアイテム', 'weight': 15, 'points': 50, 'image_url': ''},
                        {'name': 'Rアイテム', 'weight': 30, 'points': 30, 'image_url': ''},
                        {'name': 'Nアイテム', 'weight': 50, 'points': 10, 'image_url': ''}
                    ],
                    'messages': {
                        'setup': '**ガチャを回して運試し！**\n1日1回ガチャが回せるよ！',
                        'daily': '1日1回ガチャが回せます！\n下のボタンを押してガチャを実行してください。',
                        'win': None
                    },
                    'media': {'setup_image': None, 'banner_gif': None}
                },
                'battle': {
                    'enabled': True,
                    'required_role_id': None,
                    'winner_role_id': None,
                    'points_enabled': True,
                    'points_per_kill': 100,
                    'winner_points': 1000,
                    'start_delay_minutes': 2
                },
                'fortune': {'enabled': True, 'custom_messages': {}}
            },
            'updated_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat(),
            'version': 1
        }

    async def get_server_user_rankings(self, server_id: str, limit=10) -> List[Dict]:
        """サーバーのユーザーランキングを非同期で取得"""
        try:
            # DynamoDB の非同期クエリ操作
            response = await asyncio.to_thread(
                self.users_table.query,
                IndexName='ServerIndex',
                KeyConditionExpression=Key('server_id').eq(str(server_id)),
                ProjectionExpression='user_id, points',
                Limit=limit
            )
            return sorted(response.get('Items', []), key=lambda x: x.get('points', 0), reverse=True)
        except Exception as e:
            print(f"Error getting server rankings: {e}")
            return []

    async def update_user_points(self, user_id: str, server_id: str, points: int, last_gacha_date: str) -> bool:
        """既存メソッドを新しい構造に対応させる"""
        try:
            return await self.update_feature_points(
                user_id, 
                server_id, 
                'gacha', 
                points, 
                {'last_gacha_date': last_gacha_date}
            )
        except Exception as e:
            print(f"Error in update_user_points: {e}")
            return False

    async def update_feature_points(self, user_id: str, server_id: str, feature: str, points: int, metadata: dict = None) -> bool:
        """新しいポイント更新メソッド"""
        try:
            from decimal import Decimal
            pk = self._create_pk(user_id, server_id)
            
            # 既存のデータを取得
            current_data = await self.get_user_data(user_id, server_id)
            if not current_data:
                # 新規ユーザーの場合
                current_data = {
                    'pk': pk,
                    'user_id': str(user_id),
                    'server_id': str(server_id),
                    'points': {},
                    'updated_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
                }

            # ポイントデータの初期化確認
            if not isinstance(current_data.get('points'), dict):
                current_data['points'] = {}

            # 機能別ポイントの更新（Decimal型に変換）
            current_data['points'][feature] = Decimal(str(points))
            
            # 合計ポイントの再計算
            total = sum(
                Decimal(str(v)) for k, v in current_data['points'].items() 
                if k != 'total' and v is not None
            )
            current_data['points']['total'] = total

            # メタデータの更新
            if metadata:
                current_data.update(metadata)

            # 更新日時の設定
            current_data['updated_at'] = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()

            # データベースに保存
            await asyncio.to_thread(
                self.users_table.put_item,
                Item=current_data
            )
            return True
        except Exception as e:
            print(f"Error updating feature points: {e}")
            return False

    async def get_user_points(self, user_id: str, server_id: str, feature: str = None):
        """ユーザーのポイントを取得"""
        try:
            data = await self.get_user_data(user_id, server_id)
            if not data or 'points' not in data:
                return 0
            
            if feature:
                return data['points'].get(feature, 0)
            return data['points'].get('total', 0)
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
