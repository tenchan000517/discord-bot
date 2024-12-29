# create_rewards_table.py
import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

def create_rewards_table():
    try:
        # DynamoDBクライアントの初期化
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # reward_claimsテーブルの作成
        reward_claims_table = dynamodb.create_table(
            TableName='reward_claims',
            KeySchema=[
                {
                    'AttributeName': 'user_id',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'id',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'server_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_at',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'ServerIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'server_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'created_at',
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

        print("rewards_claimsテーブルを作成中...")
        reward_claims_table.meta.client.get_waiter('table_exists').wait(TableName='reward_claims')
        print("rewards_claimsテーブルの作成が完了しました！")

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("rewards_claimsテーブルは既に存在します")
        else:
            print(f"エラーが発生しました: {e}")
            raise e

if __name__ == "__main__":
    create_rewards_table()