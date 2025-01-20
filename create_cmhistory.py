import boto3
from decimal import Decimal
from datetime import datetime
from pprint import pprint

def scan_point_consumption_history():
    # DynamoDBクライアントの初期化
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('point_consumption_history')
    
    try:
        # テーブルのスキャンを実行
        response = table.scan()
        
        print("=== Point Consumption History ===")
        print(f"Total items: {response['Count']}\n")
        
        # 各レコードを整形して表示
        for item in response['Items']:
            print("Record:")
            pprint(item)
            print("-" * 50)
            
        # ページネーションがある場合の処理
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            
            for item in response['Items']:
                print("Record:")
                pprint(item)
                print("-" * 50)
                
    except Exception as e:
        print(f"Error scanning table: {str(e)}")

if __name__ == "__main__":
    scan_point_consumption_history()