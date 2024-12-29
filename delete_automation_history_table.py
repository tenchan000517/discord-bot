import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

def delete_automation_history_table():
    try:
        # DynamoDBクライアントの初期化
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # テーブルの取得
        table = dynamodb.Table('automation_history')
        
        # テーブルの削除
        table.delete()

        print("automation_historyテーブルを削除中...")
        table.meta.client.get_waiter('table_not_exists').wait(TableName='automation_history')
        print("automation_historyテーブルの削除が完了しました！")

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("automation_historyテーブルは既に存在しません")
        else:
            print(f"エラーが発生しました: {e}")
            raise e

if __name__ == "__main__":
    delete_automation_history_table()