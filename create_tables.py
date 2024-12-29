# create_tables.py
import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

def create_point_consumption_history_table():
    try:
        # DynamoDBクライアントの初期化
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # point_consumption_historyテーブルの作成
        table = dynamodb.create_table(
            TableName='point_consumption_history',
            KeySchema=[
                {
                    'AttributeName': 'server_id',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'timestamp',
                    'KeyType': 'RANGE'  # Sort key
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
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        print("point_consumption_historyテーブルを作成中...")
        table.meta.client.get_waiter('table_exists').wait(TableName='point_consumption_history')
        print("point_consumption_historyテーブルの作成が完了しました！")

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("point_consumption_historyテーブルは既に存在します")
        else:
            print(f"エラーが発生しました: {e}")
            raise e

if __name__ == "__main__":
    create_point_consumption_history_table()