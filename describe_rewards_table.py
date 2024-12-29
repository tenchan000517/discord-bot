import boto3
import os
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

def describe_rewards_table():
    try:
        # DynamoDBクライアントの初期化
        dynamodb = boto3.client('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # テーブル情報の取得
        response = dynamodb.describe_table(TableName='reward_claims')
        
        # 基本情報の表示
        print("\n=== テーブル基本情報 ===")
        print(f"テーブル名: {response['Table']['TableName']}")
        print(f"ステータス: {response['Table']['TableStatus']}")
        
        # キースキーマの表示
        print("\n=== キースキーマ ===")
        for key in response['Table']['KeySchema']:
            print(f"{key['KeyType']}: {key['AttributeName']}")
        
        # GSIの表示
        print("\n=== グローバルセカンダリインデックス ===")
        for gsi in response['Table'].get('GlobalSecondaryIndexes', []):
            print(f"\nインデックス名: {gsi['IndexName']}")
            print("キースキーマ:")
            for key in gsi['KeySchema']:
                print(f"  {key['KeyType']}: {key['AttributeName']}")
            print(f"ステータス: {gsi['IndexStatus']}")
            print(f"プロジェクションタイプ: {gsi['Projection']['ProjectionType']}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    describe_rewards_table()