# create_tables.py
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def create_dynamodb_tables():
    try:
        # DynamoDBクライアントの初期化
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # discord_usersテーブルの作成
        users_table = dynamodb.create_table(
            TableName='discord_users',
            KeySchema=[
                {
                    'AttributeName': 'pk',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'pk',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'server_id',
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
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'ServerIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'server_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # server_settingsテーブルの作成
        settings_table = dynamodb.create_table(
            TableName='server_settings',
            KeySchema=[
                {
                    'AttributeName': 'server_id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'server_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # gacha_historyテーブルの作成
        history_table = dynamodb.create_table(
            TableName='gacha_history',
            KeySchema=[
                {
                    'AttributeName': 'pk',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'timestamp',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'pk',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'timestamp',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'server_id',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'ServerTimeIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'server_id',
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

        print("テーブル作成中...")
        users_table.meta.client.get_waiter('table_exists').wait(TableName='discord_users')
        settings_table.meta.client.get_waiter('table_exists').wait(TableName='server_settings')
        history_table.meta.client.get_waiter('table_exists').wait(TableName='gacha_history')
        print("テーブルの作成が完了しました！")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        raise e  # エラーを再度発生させて詳細を確認可能に

if __name__ == "__main__":
    create_dynamodb_tables()