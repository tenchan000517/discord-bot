import boto3
from datetime import datetime
import os
import pytz
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional, Dict, List
import json
import asyncio

class AWSDatabase:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb',
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
            # DynamoDBの操作を非同期実行
            response = await asyncio.to_thread(
                self.settings_table.get_item,
                Key={'server_id': str(server_id)}
            )
            item = response.get('Item')
            
            if not item:
                # サーバーの初期設定を作成
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
            # server_idが設定に含まれていない場合は追加
            if 'server_id' not in settings:
                settings['server_id'] = str(server_id)
            
            # 更新日時を更新
            settings['updated_at'] = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
            
            # バージョンが設定されていない場合は追加
            if 'version' not in settings:
                settings['version'] = 1

            # DynamoDBの操作を非同期実行
            await asyncio.to_thread(
                self.settings_table.put_item,
                Item=settings
            )
            return True
        except Exception as e:
            print(f"Error updating server settings: {e}")
            return False

    async def update_feature_settings(self, server_id: str, feature: str, settings: Dict) -> bool:
        """特定の機能の設定のみを非同期で更新"""
        try:
            current_settings = await self.get_server_settings(server_id)
            if not current_settings:
                return False

            # feature_settingsが存在しない場合は作成
            if 'feature_settings' not in current_settings:
                current_settings['feature_settings'] = {}

            # 機能の設定を更新
            current_settings['feature_settings'][feature] = settings
            
            return await self.update_server_settings(server_id, current_settings)
        except Exception as e:
            print(f"Error updating feature settings: {e}")
            return False

    def _create_default_settings(self, server_id: str) -> Dict:
        """デフォルト設定の生成は同期的に実行（内部メソッド）"""
        # 既存のコードをそのまま維持
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
                    ],
                    'messages': {
                        'setup': '**ガチャを回して運試し！**\n1日1回ガチャが回せるよ！',
                        'daily': '1日1回ガチャが回せます！\n下のボタンを押してガチャを実行してください。',
                        'win': None
                    },
                    'media': {
                        'setup_image': None,
                        'banner_gif': None
                    }
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
                'fortune': {
                    'enabled': True,
                    'custom_messages': {}
                }
            },
            'updated_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat(),
            'version': 1
        }

    def update_server_settings(self, server_id: str, settings: Dict) -> bool:
        """サーバー設定を更新"""
        try:
            # server_idが設定に含まれていない場合は追加
            if 'server_id' not in settings:
                settings['server_id'] = str(server_id)
            
            # 更新日時を更新
            settings['updated_at'] = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
            
            # バージョンが設定されていない場合は追加
            if 'version' not in settings:
                settings['version'] = 1

            self.settings_table.put_item(Item=settings)
            return True
        except Exception as e:
            print(f"Error updating server settings: {e}")
            return False

    def update_feature_settings(self, server_id: str, feature: str, settings: Dict) -> bool:
        """特定の機能の設定のみを更新"""
        try:
            current_settings = self.get_server_settings(server_id)
            if not current_settings:
                return False

            # feature_settingsが存在しない場合は作成
            if 'feature_settings' not in current_settings:
                current_settings['feature_settings'] = {}

            # 機能の設定を更新
            current_settings['feature_settings'][feature] = settings
            
            return self.update_server_settings(server_id, current_settings)
        except Exception as e:
            print(f"Error updating feature settings: {e}")
            return False

    def get_server_user_rankings(self, server_id, limit=10):
        """サーバーのユーザーランキングを取得"""
        try:
            response = self.users_table.query(
                IndexName='ServerIndex',
                KeyConditionExpression=Key('server_id').eq(str(server_id)),
                ProjectionExpression='user_id, points',
                Limit=limit
            )
            return sorted(response['Items'], key=lambda x: x.get('points', 0), reverse=True)
        except Exception as e:
            print(f"Error getting server rankings: {e}")
            return []

    # 既存のメソッドは変更なし
    @staticmethod
    def _create_pk(user_id, server_id):
        return f"USER#{str(user_id)}#SERVER#{str(server_id)}"

    def get_user_data(self, user_id, server_id):
        try:
            pk = self._create_pk(user_id, server_id)
            response = self.users_table.get_item(
                Key={'pk': pk}
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error getting user data: {e}")
            return None

    def update_user_points(self, user_id, server_id, points, last_gacha_date):
        try:
            pk = self._create_pk(user_id, server_id)
            self.users_table.put_item(
                Item={
                    'pk': pk,
                    'user_id': str(user_id),
                    'server_id': str(server_id),
                    'points': points,
                    'last_gacha_date': last_gacha_date,
                    'updated_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error updating user points: {e}")
            return False