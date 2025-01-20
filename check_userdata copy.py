import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
from decimal import Decimal
from datetime import datetime

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

def check_table_exists(dynamodb, table_name):
    try:
        dynamodb.Table(table_name).table_status
        return True
    except Exception:
        return False

def check_user_data(user_id):
    # DynamoDBクライアントの初期化
    dynamodb = boto3.resource('dynamodb')
    
    # 確認するテーブルのリスト
    tables = [
        'discord_users',
        'point_consumption_history',
        'server_settings'
    ]
    
    print("=== テーブル存在確認 ===")
    existing_tables = {}
    for table_name in tables:
        exists = check_table_exists(dynamodb, table_name)
        existing_tables[table_name] = exists
        print(f"{table_name}: {'存在します' if exists else '存在しません'}")
    
    results = {
        'user_data': [],
        'consumption_history': [],
        'related_servers': set()
    }

    try:
        # discord_usersテーブルからのデータ取得
        if existing_tables['discord_users']:
            users_table = dynamodb.Table('discord_users')
            
            # Scanを使用してユーザーIDでフィルタリング
            print(f"\n=== ユーザー {user_id} のポイントデータ ===")
            scan_kwargs = {
                'FilterExpression': Attr('user_id').eq(user_id)
            }
            
            done = False
            start_key = None
            while not done:
                if start_key:
                    scan_kwargs['ExclusiveStartKey'] = start_key
                response = users_table.scan(**scan_kwargs)
                
                if response['Items']:
                    for item in response['Items']:
                        formatted_item = {
                            'pk': item.get('pk', 'N/A'),
                            'points': item.get('points', 'N/A'),
                            'server_id': item.get('server_id', 'N/A'),
                            'unit_id': item.get('unit_id', 'N/A'),
                            'displayName': item.get('displayName', 'N/A'),
                        }
                        results['user_data'].append(formatted_item)
                        if item.get('server_id'):
                            results['related_servers'].add(item.get('server_id'))
                        
                        print("\nレコード詳細:")
                        print(f"PK: {formatted_item['pk']}")
                        print(f"ポイント: {formatted_item['points']}")
                        print(f"サーバーID: {formatted_item['server_id']}")
                        print(f"ユニットID: {formatted_item['unit_id']}")
                        print(f"表示名: {formatted_item['displayName']}")
                        print("-" * 50)
                
                start_key = response.get('LastEvaluatedKey')
                done = start_key is None
            
            if not results['user_data']:
                print("ポイントデータが見つかりませんでした")

        # point_consumption_historyテーブルからのデータ取得
        if existing_tables['point_consumption_history']:
            history_table = dynamodb.Table('point_consumption_history')
            
            print(f"\n=== ユーザー {user_id} のポイント消費履歴 ===")
            scan_kwargs = {
                'FilterExpression': Attr('user_id').eq(user_id)
            }
            
            done = False
            start_key = None
            history_found = False
            while not done:
                if start_key:
                    scan_kwargs['ExclusiveStartKey'] = start_key
                response = history_table.scan(**scan_kwargs)
                
                if response['Items']:
                    history_found = True
                    for item in response['Items']:
                        results['consumption_history'].append(item)
                        if item.get('server_id'):
                            results['related_servers'].add(item.get('server_id'))
                        
                        print("\n消費履歴レコード:")
                        print(f"サーバーID: {item.get('server_id', 'N/A')}")
                        print(f"タイムスタンプ: {item.get('timestamp', 'N/A')}")
                        print(f"消費ポイント: {item.get('points', 'N/A')}")
                        print(f"理由: {item.get('reason', 'N/A')}")
                        print("-" * 50)
                
                start_key = response.get('LastEvaluatedKey')
                done = start_key is None
            
            if not history_found:
                print("ポイント消費履歴が見つかりませんでした")

        # 関連するサーバーの設定を取得
        if existing_tables['server_settings'] and results['related_servers']:
            settings_table = dynamodb.Table('server_settings')
            
            print("\n=== 関連サーバーの設定 ===")
            for server_id in results['related_servers']:
                try:
                    response = settings_table.get_item(
                        Key={'server_id': server_id}
                    )
                    if 'Item' in response:
                        print(f"\nサーバー {server_id} の設定:")
                        settings = response['Item']
                        if 'global_settings' in settings:
                            print("グローバル設定:")
                            print(json.dumps(settings['global_settings'], 
                                          indent=2, cls=DecimalEncoder, 
                                          ensure_ascii=False))
                            print("-" * 50)
                except Exception as e:
                    print(f"サーバー {server_id} の設定取得中にエラー: {str(e)}")

        # 結果をJSONファイルとして保存
        output_file = f'user_{user_id}_comprehensive_data.json'
        results['related_servers'] = list(results['related_servers'])  # setをリストに変換
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, cls=DecimalEncoder, ensure_ascii=False)
        print(f"\n結果を {output_file} に保存しました")
        
        return results
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return None

if __name__ == "__main__":
    TARGET_USER_ID = "976427276340166696"  # 検査したいユーザーID
    results = check_user_data(TARGET_USER_ID)