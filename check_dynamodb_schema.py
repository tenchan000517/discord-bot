import boto3
import os
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

def get_table_details(table_name: str, dynamodb) -> dict:
    """テーブルの詳細情報を取得"""
    table = dynamodb.Table(table_name)
    
    # テーブルの詳細情報を取得
    response = table.meta.client.describe_table(
        TableName=table_name
    )
    
    return response['Table']

def get_table_items(table_name: str, dynamodb, limit: int = 5) -> list:
    """テーブルのデータを取得（最大 limit 件まで）"""
    table = dynamodb.Table(table_name)
    
    # データをスキャン
    response = table.scan(Limit=limit)
    items = response.get('Items', [])
    
    return items

def analyze_table_schema(table_details: dict) -> None:
    """テーブルのスキーマを分析して表示"""
    print(f"\n=== {table_details['TableName']} の詳細情報 ===")
    print("\n--- 基本情報 ---")
    print(f"テーブル名: {table_details['TableName']}")
    print(f"ステータス: {table_details['TableStatus']}")
    print(f"アイテム数: {table_details.get('ItemCount', 'N/A')}")
    print(f"サイズ(バイト): {table_details.get('TableSizeBytes', 'N/A')}")

    print("\n--- キースキーマ ---")
    for key in table_details['KeySchema']:
        print(f"  - {key['AttributeName']}: {key['KeyType']}")

    print("\n--- 属性定義 ---")
    for attr in table_details['AttributeDefinitions']:
        print(f"  - {attr['AttributeName']}: {attr['AttributeType']}")

    if 'GlobalSecondaryIndexes' in table_details:
        print("\n--- グローバルセカンダリインデックス ---")
        for gsi in table_details['GlobalSecondaryIndexes']:
            print(f"  インデックス名: {gsi['IndexName']}")
            print("  キースキーマ:")
            for key in gsi['KeySchema']:
                print(f"    - {key['AttributeName']}: {key['KeyType']}")

    if 'LocalSecondaryIndexes' in table_details:
        print("\n--- ローカルセカンダリインデックス ---")
        for lsi in table_details['LocalSecondaryIndexes']:
            print(f"  インデックス名: {lsi['IndexName']}")
            print("  キースキーマ:")
            for key in lsi['KeySchema']:
                print(f"    - {key['AttributeName']}: {key['KeyType']}")

    print("\n--- プロビジョニング設定 ---")
    if 'ProvisionedThroughput' in table_details:
        pt = table_details['ProvisionedThroughput']
        print(f"  読み込みキャパシティーユニット: {pt['ReadCapacityUnits']}")
        print(f"  書き込みキャパシティーユニット: {pt['WriteCapacityUnits']}")
    else:
        print("  オンデマンドモード")

    print("\n--- ストリーム設定 ---")
    if 'StreamSpecification' in table_details:
        print(f"  ストリーム有効: {table_details['StreamSpecification']['StreamEnabled']}")
        if table_details['StreamSpecification']['StreamEnabled']:
            print(f"  ストリームビュータイプ: {table_details['StreamSpecification']['StreamViewType']}")
    else:
        print("  ストリーム無効")

def analyze_table_items(table_name: str, items: list) -> None:
    """テーブル内のデータを表示"""
    print(f"\n=== {table_name} のデータ内容 ===")
    if not items:
        print("  データが見つかりませんでした。")
    else:
        for idx, item in enumerate(items, start=1):
            print(f"--- アイテム {idx} ---")
            pprint(item)

def main():
    try:
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # 確認したいテーブル名のリスト
        tables = ['discord_users', 'gacha_history', 'server_settings']

        for table_name in tables:
            try:
                # テーブルのスキーマを分析
                table_details = get_table_details(table_name, dynamodb)
                analyze_table_schema(table_details)

                # テーブル内のデータを取得して表示
                items = get_table_items(table_name, dynamodb)
                analyze_table_items(table_name, items)
            except Exception as e:
                print(f"\nError analyzing table {table_name}: {str(e)}")

    except Exception as e:
        print(f"Error connecting to DynamoDB: {str(e)}")

if __name__ == "__main__":
    main()
