import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import time

load_dotenv()

def add_status_index():
    try:
        # DynamoDBクライアントの初期化
        dynamodb = boto3.client('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # StatusIndexの追加
        response = dynamodb.update_table(
            TableName='reward_claims',
            AttributeDefinitions=[
                {'AttributeName': 'status', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexUpdates=[
                {
                    'Create': {
                        'IndexName': 'StatusIndex',
                        'KeySchema': [
                            {'AttributeName': 'status', 'KeyType': 'HASH'},
                            {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                }
            ]
        )
        
        print("StatusIndexを追加中...")
        
        # テーブルのステータスが ACTIVE になるまで待機
        while True:
            response = dynamodb.describe_table(TableName='reward_claims')
            status = response['Table']['TableStatus']
            if status == 'ACTIVE':
                # すべてのGSIが ACTIVE になっているか確認
                all_gsi_active = True
                for gsi in response['Table'].get('GlobalSecondaryIndexes', []):
                    if gsi['IndexStatus'] != 'ACTIVE':
                        all_gsi_active = False
                        break
                if all_gsi_active:
                    break
            print("インデックスの作成中... しばらくお待ちください")
            time.sleep(5)  # 5秒待機

        print("StatusIndexの追加が完了しました！")

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("StatusIndexは既に存在します")
        elif e.response['Error']['Code'] == 'ValidationException' and 'already exists' in str(e):
            print("StatusIndexは既に存在します")
        else:
            print(f"エラーが発生しました: {e}")
            raise e

if __name__ == "__main__":
    add_status_index()