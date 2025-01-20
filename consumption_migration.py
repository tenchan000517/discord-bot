import boto3
from decimal import Decimal
import random
from datetime import datetime

def update_consumption_history():
    # DynamoDBクライアントの初期化
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('point_consumption_history')
    
    # 対象のサーバーID
    target_server_id = '1236319711113777233'
    
    try:
        # 対象サーバーのレコードを取得
        response = table.scan(
            FilterExpression='server_id = :sid',
            ExpressionAttributeValues={
                ':sid': target_server_id
            }
        )
        
        print(f"Found {response['Count']} records to update")
        
        # 各レコードを更新
        for item in response['Items']:
            # ランダムにunit_idを割り当て（1か2）
            new_unit_id = str(random.randint(1, 2))
            
            # レコードを更新 - 正しいキーを使用
            table.update_item(
                Key={
                    'server_id': item['server_id'],
                    'timestamp': item['timestamp']
                },
                UpdateExpression='SET unit_id = :unit_id',
                ExpressionAttributeValues={
                    ':unit_id': new_unit_id
                }
            )
            
            print(f"Updated record for user {item.get('user_id', 'unknown')} at {item['timestamp']} with unit_id {new_unit_id}")
        
        print("\n=== Update Summary ===")
        print(f"Total records updated: {response['Count']}")
        
        # 更新後の確認のためのスキャン
        verification = table.scan(
            FilterExpression='server_id = :sid',
            ExpressionAttributeValues={
                ':sid': target_server_id
            }
        )
        
        records_with_unit_id = sum(1 for item in verification['Items'] if 'unit_id' in item)
        print(f"Records with unit_id after update: {records_with_unit_id}")
        
    except Exception as e:
        print(f"Error updating records: {str(e)}")

if __name__ == "__main__":
    print("Starting update process...")
    update_consumption_history()
    print("Process completed.")