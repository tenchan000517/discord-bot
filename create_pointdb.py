import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import time

def recreate_point_consumption_table():
    try:
        # DynamoDBクライアントの初期化
        dynamodb = boto3.client('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # まず既存のテーブルを削除
        print("既存のテーブルを削除中...")
        try:
            dynamodb.delete_table(TableName='point_consumption_history')
            print("テーブルの削除を待機中...")
            waiter = dynamodb.get_waiter('table_not_exists')
            waiter.wait(TableName='point_consumption_history')
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise e

        # 少し待機（テーブル削除完了を確実にするため）
        time.sleep(10)

        # 新しいテーブルを作成
        print("新しいテーブルを作成中...")
        dynamodb.create_table(
            TableName='point_consumption_history',
            KeySchema=[
                {
                    'AttributeName': 'server_id',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'timestamp',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'server_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'status',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        print("テーブルの作成を待機中...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName='point_consumption_history')
        print("point_consumption_historyテーブルの再作成が完了しました！")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        raise e

if __name__ == "__main__":
    load_dotenv()
    recreate_point_consumption_table()