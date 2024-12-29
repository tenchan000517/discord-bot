import boto3
from datetime import datetime
import os
import pytz
from boto3.dynamodb.conditions import Key, Attr
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
        # テーブル参照の初期化
        self.users_table = self.dynamodb.Table('discord_users')
        self.settings_table = self.dynamodb.Table('server_settings')
        self.automation_rules_table = self.dynamodb.Table('automation_rules')
        self.point_consumption_history_table = self.dynamodb.Table('point_consumption_history')
        self.reward_claims_table = self.dynamodb.Table('reward_claims')
        
    # Basic Server Operations
    async def register_server(self, server_id: str):
            """サーバーIDをserver_settingsテーブルに登録
            このメソッドは直接呼び出さず、register_server_with_settingsを使用してください。
            """
            try:
                # 既存の設定を確認
                response = await asyncio.to_thread(
                    self.settings_table.get_item,
                    Key={'server_id': str(server_id)}
                )
                return 'Item' not in response  # 新規登録が必要な場合はTrue
            except Exception as e:
                print(f"Error checking server registration {server_id}: {e}")
                raise

    async def register_server_with_settings(self, server_id: str, settings_manager) -> bool:
        """サーバーの登録と初期設定を行う"""
        try:
            needs_registration = await self.register_server(str(server_id))
            if needs_registration:
                # 新規サーバーの場合、デフォルト設定を作成
                success = await settings_manager.create_default_settings(str(server_id))
                if success:
                    print(f"Successfully registered new server: {server_id}")
                    return True
                else:
                    print(f"Failed to create default settings for server: {server_id}")
                    return False
            return True  # 既に登録済みの場合
        except Exception as e:
            print(f"Error registering server {server_id}: {e}")
            return False

    async def register_existing_servers(self, guilds, settings_manager):
        """既存のサーバーを一括登録"""
        for guild in guilds:
            try:
                await self.register_server_with_settings(str(guild.id), settings_manager)
                print(f"Registered existing server: {guild.name} (ID: {guild.id})")
            except Exception as e:
                print(f"Error registering existing server {guild.id}: {e}")

    async def remove_server(self, server_id: str):
        """サーバーIDをserver_settingsテーブルから削除"""
        try:
            await asyncio.to_thread(
                self.settings_table.delete_item,
                Key={'server_id': str(server_id)}
            )
            print(f"Successfully removed server: {server_id}")
            return True
        except Exception as e:
            print(f"Error removing server {server_id}: {e}")
            raise

    # User Points Management
    async def get_user_points(self, user_id: str, server_id: str) -> int:
        """ユーザーの合計ポイントを取得"""
        try:
            data = await self.get_user_data(user_id, server_id)
            return int(data.get('points', 0)) if data else 0
        except Exception as e:
            print(f"Error getting user points: {e}")
            return 0

    async def update_user_points(self, user_id: str, server_id: str, points: int) -> bool:
        """ユーザーのポイントを更新"""
        try:
            return await self.update_feature_points(user_id, server_id, points)
        except Exception as e:
            print(f"Error in update_user_points: {e}")
            return False

    async def update_feature_points(self, user_id: str, server_id: str, points: int) -> bool:
        """ユーザーの機能別ポイントを更新"""
        try:
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

    # Rankings Management
    async def get_server_user_rankings(self, server_id: str) -> List[Dict]:
        """サーバー内のユーザーランキングを取得"""
        try:
            response = await asyncio.to_thread(self.users_table.scan)
            server_rankings = []
            
            for item in response.get('Items', []):
                pk = item.get('pk', '')
                if f'SERVER#{server_id}' in pk:
                    user_id = pk.split('#')[1]
                    points = int(float(item.get('points', 0)))
                    server_rankings.append({
                        'user_id': user_id,
                        'points': points
                    })
            
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
            response = await asyncio.to_thread(self.users_table.scan)
            user_points = {}
            
            for item in response.get('Items', []):
                pk = item.get('pk', '')
                if 'USER#' in pk:
                    user_id = pk.split('#')[1]
                    points = int(float(item.get('points', 0)))
                    user_points[user_id] = user_points.get(user_id, 0) + points
            
            rankings = [
                {'user_id': user_id, 'points': points}
                for user_id, points in user_points.items()
            ]
            
            rankings.sort(key=lambda x: x['points'], reverse=True)
            print(f"[DEBUG] 全サーバーの総ユーザー数: {len(rankings)}")
            return rankings
                
        except Exception as e:
            print(f"Error getting all rankings: {str(e)}")
            print(traceback.format_exc())
            return []
        
    # Automation Rules Management
    async def get_automation_rules(self, server_id: str) -> List[Dict]:
        """サーバーのオートメーションルールを取得"""
        try:
            response = await asyncio.to_thread(
                self.automation_rules_table.query,
                KeyConditionExpression=Key('server_id').eq(str(server_id))
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting automation rules: {e}")
            return []

    async def get_automation_rule(self, server_id: str, rule_id: str) -> Optional[Dict]:
        """特定のオートメーションルールを取得"""
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

    async def save_automation_rule(self, rule_data: dict) -> bool:
        """オートメーションルールを保存"""
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
        """オートメーションルールを削除"""
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

    # Rewards Management
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

    async def get_user_rewards(self, user_id: str, server_id: str, status: Optional[str] = None) -> List[Dict]:
        """ユーザーの報酬履歴を取得"""
        try:
            key_condition = Key('user_id').eq(str(user_id))
            filter_expression = None

            if status:
                filter_expression = Attr('status').eq(status)
                if server_id:
                    filter_expression = filter_expression & Attr('server_id').eq(str(server_id))
            elif server_id:
                filter_expression = Attr('server_id').eq(str(server_id))

            kwargs = {
                'KeyConditionExpression': key_condition,
                'ScanIndexForward': False
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

    async def get_rewards_by_status(self, status: str, server_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
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

    # Point Consumption Management
    async def create_consumption_request(self, server_id: str, user_id: str, points: int, thread_id: Optional[str] = None) -> Optional[Dict]:
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

    async def update_consumption_status(self, server_id: str, timestamp: str, status: str, admin_id: str, reason: Optional[str] = None) -> bool:
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

    # Utility Methods
    @staticmethod
    def _create_pk(user_id: str, server_id: str) -> str:
        """プライマリキーを生成"""
        return f"USER#{user_id}#SERVER#{server_id}"

    async def get_user_data(self, user_id: str, server_id: str) -> Optional[Dict]:
        """ユーザーのデータを取得"""
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