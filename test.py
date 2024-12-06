import boto3
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# テスト用のコード
def test_aws_connection():
    try:
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # 利用可能なテーブル一覧を取得
        tables = list(dynamodb.tables.all())
        print("接続成功！")
        print(f"利用可能なテーブル: {[table.name for table in tables]}")
        return True
    except Exception as e:
        print(f"接続エラー: {e}")
        return False

if __name__ == "__main__":
    test_aws_connection()