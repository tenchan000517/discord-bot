import boto3
from boto3.dynamodb.conditions import Key
import json
from datetime import datetime
import os
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

class DynamoDBChecker:
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

    def check_table_exists(self, table_name):
        try:
            table = self.dynamodb.Table(table_name)
            table.table_status
            return True
        except:
            return False

    def scan_table(self, table_name):
        """テーブルの全データを取得"""
        table = self.dynamodb.Table(table_name)
        try:
            response = table.scan()
            items = response['Items']
            
            # 全アイテムを取得（ページネーション対応）
            while 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response['Items'])
                
            return items
        except Exception as e:
            print(f"Error scanning table {table_name}: {str(e)}")
            return []

    def get_server_points(self, server_id):
        """特定のサーバーのポイントデータを取得"""
        table = self.dynamodb.Table('user_points')
        try:
            response = table.query(
                KeyConditionExpression=Key('server_id').eq(server_id)
            )
            return response['Items']
        except Exception as e:
            print(f"Error getting server points: {str(e)}")
            return []

    def get_point_history(self, server_id=None):
        """ポイント履歴を取得"""
        table = self.dynamodb.Table('point_consumption_history')
        try:
            if server_id:
                response = table.query(
                    KeyConditionExpression=Key('server_id').eq(server_id)
                )
            else:
                response = table.scan()
            return response['Items']
        except Exception as e:
            print(f"Error getting point history: {str(e)}")
            return []

    def get_server_settings(self, server_id):
        """サーバー設定を取得"""
        table = self.dynamodb.Table('server_settings')
        try:
            response = table.get_item(
                Key={'server_id': server_id}
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error getting server settings: {str(e)}")
            return None

def print_formatted(title, data):
    """データを見やすく表示"""
    print(f"\n=== {title} ===")
    try:
        print(json.dumps(data, indent=2, ensure_ascii=False, cls=DecimalEncoder))
    except Exception as e:
        print(f"Error formatting data: {str(e)}")
        print("Raw data:", data)
    print("=" * 50)

def analyze_consumption_history(history_data):
    """ポイント消費履歴の分析"""
    print("\n=== ポイント消費履歴の分析 ===")
    
    # ステータス別の集計
    status_count = {}
    for item in history_data:
        status = item.get('status', 'unknown')
        status_count[status] = status_count.get(status, 0) + 1
    
    print("\nステータス別件数:")
    for status, count in status_count.items():
        print(f"{status}: {count}件")

    # 未処理の申請を表示
    print("\n未処理の申請:")
    pending_items = [item for item in history_data if item.get('status') == 'pending']
    for item in pending_items:
        print(f"- ユーザー: {item.get('user_id')}, 時間: {item.get('timestamp')}, ポイント: {item.get('points')}")

def main():
    server_id = input("確認したいサーバーIDを入力してください（Enterで全て確認）: ").strip()
    
    checker = DynamoDBChecker()
    
    tables = [
        'user_points',
        'point_consumption_history',
        'server_settings',
    ]
    
    print("\n=== テーブル存在確認 ===")
    for table in tables:
        exists = checker.check_table_exists(table)
        print(f"{table}: {'存在します' if exists else '存在しません'}")
    
    if server_id:
        points = checker.get_server_points(server_id)
        print_formatted(f"サーバー {server_id} のポイントデータ", points)
        
        history = checker.get_point_history(server_id)
        print_formatted(f"サーバー {server_id} のポイント履歴", history)
        if history:
            analyze_consumption_history(history)
        
        settings = checker.get_server_settings(server_id)
        print_formatted(f"サーバー {server_id} の設定", settings)
    else:
        for table in tables:
            if checker.check_table_exists(table):
                data = checker.scan_table(table)
                print_formatted(f"{table} の全データ", data)
                if table == 'point_consumption_history' and data:
                    analyze_consumption_history(data)

if __name__ == "__main__":
    main()