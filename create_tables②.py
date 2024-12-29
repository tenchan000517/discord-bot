# create_automation_tables.py
import boto3
import os
import time
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

def delete_table_if_exists(dynamodb, table_name):
    try:
        table = dynamodb.Table(table_name)
        table.delete()
        print(f"テーブル {table_name} の削除を開始しました...")
        table.meta.client.get_waiter('table_not_exists').wait(TableName=table_name)
        print(f"テーブル {table_name} を削除しました")
        time.sleep(5)  # 削除完了後の安全待機
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"テーブル {table_name} は存在しません")
        else:
            raise e

def create_automation_tables():
    try:
        # DynamoDBクライアントの初期化
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # 既存のテーブルを削除
        delete_table_if_exists(dynamodb, 'automation_rules')
        delete_table_if_exists(dynamodb, 'automation_history')

        # automation_rulesテーブルの作成
        automation_rules_table = dynamodb.create_table(
            TableName='automation_rules',
            KeySchema=[
                {
                    'AttributeName': 'server_id',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'id',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'server_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # automation_historyテーブルの作成
        automation_history_table = dynamodb.create_table(
            TableName='automation_history',
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
                    'AttributeName': 'rule_id',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'RuleIdIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'rule_id',
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

        print("オートメーションテーブル作成中...")
        automation_rules_table.meta.client.get_waiter('table_exists').wait(TableName='automation_rules')
        automation_history_table.meta.client.get_waiter('table_exists').wait(TableName='automation_history')
        print("オートメーションテーブルの作成が完了しました！")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        raise e

if __name__ == "__main__":
    create_automation_tables()