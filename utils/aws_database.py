# utils/aws_database.py
import boto3
from datetime import datetime
import os
import pytz
from boto3.dynamodb.conditions import Key, Attr

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

    def get_server_settings(self, server_id):
        try:
            response = self.settings_table.get_item(
                Key={'server_id': str(server_id)}
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error getting server settings: {e}")
            return None

    def update_server_settings(self, server_id, settings):
        try:
            self.settings_table.put_item(
                Item={
                    'server_id': str(server_id),
                    'settings': settings,
                    'updated_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error updating server settings: {e}")
            return False

    def record_gacha_history(self, user_id, server_id, result_item, points):
        try:
            current_time = int(datetime.now().timestamp())
            pk = self._create_pk(user_id, server_id)
            self.history_table.put_item(
                Item={
                    'pk': pk,
                    'timestamp': current_time,
                    'user_id': str(user_id),
                    'server_id': str(server_id),
                    'item_name': result_item['name'],
                    'points': points,
                    'created_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error recording gacha history: {e}")
            return False

    # 新しい機能のためのメソッド追加
    def get_server_user_rankings(self, server_id, limit=10):
        try:
            response = self.users_table.query(
                IndexName='ServerIndex',
                KeyConditionExpression=Key('server_id').eq(str(server_id)),
                ProjectionExpression='user_id, points',
                Limit=limit
            )
            return sorted(response['Items'], key=lambda x: x['points'], reverse=True)
        except Exception as e:
            print(f"Error getting server rankings: {e}")
            return []

    def get_user_gacha_history(self, user_id, server_id, limit=10):
        try:
            pk = self._create_pk(user_id, server_id)
            response = self.history_table.query(
                KeyConditionExpression=Key('pk').eq(pk),
                ScanIndexForward=False,  # 新しい順
                Limit=limit
            )
            return response['Items']
        except Exception as e:
            print(f"Error getting user gacha history: {e}")
            return []
        
    def get_latest_fortune(self, user_id, server_id):
        """ユーザーの最新の占い結果を取得"""
        try:
            pk = self._create_pk(user_id, server_id)
            response = self.history_table.query(
                KeyConditionExpression=Key('pk').eq(pk),
                FilterExpression=Attr('fortune_type').exists(),
                ScanIndexForward=False,  # 新しい順
                Limit=1
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception as e:
            print(f"Error getting latest fortune: {e}")
            return None

    def record_fortune(self, user_id, server_id, fortune_type):
        """占い結果を記録"""
        try:
            pk = self._create_pk(user_id, server_id)
            self.history_table.put_item(
                Item={
                    'pk': pk,
                    'timestamp': int(datetime.now().timestamp()),
                    'user_id': str(user_id),
                    'server_id': str(server_id),
                    'fortune_type': fortune_type,
                    'created_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error recording fortune: {e}")
            return False

    def get_fortune_history_stats(self, user_id, server_id, limit=30):
        """ユーザーの占い履歴統計を取得"""
        try:
            pk = self._create_pk(user_id, server_id)
            response = self.history_table.query(
                KeyConditionExpression=Key('pk').eq(pk),
                FilterExpression=Attr('fortune_type').exists(),
                ScanIndexForward=False,
                Limit=limit
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting fortune history stats: {e}")
            return []