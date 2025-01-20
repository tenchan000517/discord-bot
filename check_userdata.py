import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
from datetime import datetime
import os
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

class DiscordUsersChecker:
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.table = self.dynamodb.Table('discord_users')

    def get_all_users(self):
        """全ユーザーデータを取得"""
        try:
            response = self.table.scan()
            items = response['Items']
            
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response['Items'])
                
            return items
        except Exception as e:
            print(f"Error scanning table: {str(e)}")
            return []

    def get_user_data(self, user_id=None, server_id=None):
        """特定のユーザーまたはサーバーのデータを取得"""
        try:
            filter_expression = None
            if user_id and server_id:
                filter_expression = Attr('user_id').eq(user_id) & Attr('server_id').eq(server_id)
            elif user_id:
                filter_expression = Attr('user_id').eq(user_id)
            elif server_id:
                filter_expression = Attr('server_id').eq(server_id)

            if filter_expression:
                response = self.table.scan(FilterExpression=filter_expression)
            else:
                response = self.table.scan()

            items = response['Items']
            while 'LastEvaluatedKey' in response:
                if filter_expression:
                    response = self.table.scan(
                        FilterExpression=filter_expression,
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                else:
                    response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response['Items'])

            return items
        except Exception as e:
            print(f"Error getting user data: {str(e)}")
            return []

def print_raw_data(data, title="Raw Data"):
    """生のデータを表示"""
    print(f"\n=== {title} ===")
    print(json.dumps(data, indent=2, ensure_ascii=False, cls=DecimalEncoder))
    print("=" * 50)

def print_formatted_data(data, title="Formatted Data"):
    """整形したデータを表示"""
    print(f"\n=== {title} ===")
    if not data:
        print("データがありません")
        print("=" * 50)
        return

    # サーバーごとにデータを整理
    server_data = {}
    for item in data:
        server_id = item.get('server_id')
        if server_id not in server_data:
            server_data[server_id] = []
        server_data[server_id].append(item)

    # サーバーごとに表示
    for server_id, items in server_data.items():
        print(f"\nサーバー: {server_id}")
        print("-" * 30)
        
        for item in items:
            print("\nユーザーデータ:")
            print(f"ユーザーID: {item.get('user_id', 'N/A')}")
            print(f"ポイント: {item.get('points', 'N/A')}")
            print(f"ユニットID: {item.get('unit_id', 'N/A')}")
            if item.get('displayName'):
                print(f"表示名: {item.get('displayName')}")
            if item.get('pk'):
                print(f"PK: {item.get('pk')}")
            print("-" * 20)
    
    print("=" * 50)

def main():
    checker = DiscordUsersChecker()
    
    while True:
        print("\n1: 全データ確認")
        print("2: 特定ユーザーのデータ確認")
        print("3: 特定サーバーのデータ確認")
        print("4: 特定ユーザーの特定サーバーでのデータ確認")
        print("0: 終了")
        
        choice = input("\n選択してください: ")
        
        if choice == "0":
            break
        elif choice == "1":
            data = checker.get_all_users()
            print_raw_data(data, "全ユーザーデータ (Raw)")
            print_formatted_data(data, "全ユーザーデータ (Formatted)")
        elif choice == "2":
            user_id = input("ユーザーIDを入力してください: ")
            data = checker.get_user_data(user_id=user_id)
            print_raw_data(data, f"ユーザー {user_id} のデータ (Raw)")
            print_formatted_data(data, f"ユーザー {user_id} のデータ (Formatted)")
        elif choice == "3":
            server_id = input("サーバーIDを入力してください: ")
            data = checker.get_user_data(server_id=server_id)
            print_raw_data(data, f"サーバー {server_id} のデータ (Raw)")
            print_formatted_data(data, f"サーバー {server_id} のデータ (Formatted)")
        elif choice == "4":
            user_id = input("ユーザーIDを入力してください: ")
            server_id = input("サーバーIDを入力してください: ")
            data = checker.get_user_data(user_id=user_id, server_id=server_id)
            print_raw_data(data, f"ユーザー {user_id} のサーバー {server_id} でのデータ (Raw)")
            print_formatted_data(data, f"ユーザー {user_id} のサーバー {server_id} でのデータ (Formatted)")
        else:
            print("無効な選択です")

if __name__ == "__main__":
    main()