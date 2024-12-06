import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def list_tables():
    try:
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # 全テーブルのリストを取得
        tables = list(dynamodb.tables.all())
        print("作成されたテーブル:")
        for table in tables:
            print(f"- {table.name}")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")

def list_tables():
    try:
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # テーブル一覧の取得
        tables = list(dynamodb.tables.all())
        print("\n=== DynamoDB テーブル一覧 ===")
        for table in tables:
            print(f"テーブル名: {table.name}")
            # テーブルの詳細情報を取得
            table_detail = table.meta.client.describe_table(TableName=table.name)
            print(f"ステータス: {table_detail['Table']['TableStatus']}")
            print("キースキーマ:", table_detail['Table']['KeySchema'])
            print("-" * 50)

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    list_tables()