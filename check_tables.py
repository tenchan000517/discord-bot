import boto3
import os
from dotenv import load_dotenv
from pprint import pprint

def check_table_structure():
    try:
        # DynamoDBクライアントの初期化
        dynamodb = boto3.client('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # テーブルの詳細を取得
        response = dynamodb.describe_table(
            TableName='point_consumption_history'
        )
        
        print("=== 現在のテーブル構造 ===")
        pprint(response['Table'])
        
        # インデックスの確認
        if 'GlobalSecondaryIndexes' in response['Table']:
            print("\n=== 現在のグローバルセカンダリインデックス ===")
            for index in response['Table']['GlobalSecondaryIndexes']:
                print(f"\nインデックス名: {index['IndexName']}")
                print("キースキーマ:")
                pprint(index['KeySchema'])

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    load_dotenv()
    check_table_structure()