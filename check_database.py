import boto3
import os
from dotenv import load_dotenv
from pprint import pprint
from decimal import Decimal
from datetime import datetime
import json

def check_database():
    try:
        # DynamoDBクライアントの初期化
        dynamodb = boto3.client('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # DynamoDBリソースの初期化（テーブルスキャン用）
        dynamodb_resource = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # 利用可能なテーブル一覧を取得
        tables = dynamodb.list_tables()
        print("=== 利用可能なテーブル ===")
        for table in tables['TableNames']:
            print(f"- {table}")
        print()

        # 各テーブルの詳細を確認
        for table_name in tables['TableNames']:
            print(f"\n=== テーブル: {table_name} の分析 ===")
            
            # テーブル構造の取得
            table_info = dynamodb.describe_table(TableName=table_name)['Table']
            
            print("\n--- テーブル構造 ---")
            print("プライマリキー:")
            pprint(table_info['KeySchema'])
            
            print("\n属性定義:")
            pprint(table_info['AttributeDefinitions'])
            
            # GSIの確認
            if 'GlobalSecondaryIndexes' in table_info:
                print("\nグローバルセカンダリインデックス:")
                for index in table_info['GlobalSecondaryIndexes']:
                    print(f"\n  {index['IndexName']}:")
                    print("  キースキーマ:")
                    pprint(index['KeySchema'])

            # テーブルデータの分析
            table = dynamodb_resource.Table(table_name)
            items = table.scan()['Items']
            
            print(f"\n--- データ分析 ---")
            print(f"総レコード数: {len(items)}")
            
            # データ構造の分析
            analysis = {
                'unique_keys': set(),
                'data_types': {},
                'server_ids': set(),
                'user_ids': set(),
                'point_samples': [],
                'unit_ids': set()
            }
            
            for item in items:
                # キーの収集
                analysis['unique_keys'].update(item.keys())
                
                # サーバーIDとユーザーIDの収集
                if 'server_id' in item:
                    analysis['server_ids'].add(item['server_id'])
                if 'user_id' in item:
                    analysis['user_ids'].add(item['user_id'])
                if 'unit_id' in item:
                    analysis['unit_ids'].add(item['unit_id'])
                
                # データ型の分析
                for key, value in item.items():
                    if key not in analysis['data_types']:
                        analysis['data_types'][key] = set()
                    analysis['data_types'][key].add(type(value).__name__)
                    
                    # ポイント関連データのサンプル収集
                    if 'point' in key.lower():
                        if len(analysis['point_samples']) < 5:  # 最大5件まで
                            analysis['point_samples'].append({
                                'key': key,
                                'value': str(value),
                                'type': type(value).__name__
                            })

            print("\nユニークなキー:")
            pprint(sorted(analysis['unique_keys']))
            
            print("\nユニークなサーバー数:", len(analysis['server_ids']))
            print("ユニークなユーザー数:", len(analysis['user_ids']))
            if analysis['unit_ids']:
                print("ユニークなユニットID:", sorted(analysis['unit_ids']))
            
            print("\nフィールド別データ型:")
            for key, types in sorted(analysis['data_types'].items()):
                print(f"{key}: {sorted(types)}")
            
            if analysis['point_samples']:
                print("\nポイントデータのサンプル:")
                pprint(analysis['point_samples'])

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    load_dotenv()
    check_database()