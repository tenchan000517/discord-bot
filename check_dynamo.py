import boto3
from boto3.dynamodb.conditions import Key
import json
from datetime import datetime
import os
from decimal import Decimal
import time

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

class DynamoDBChecker:
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.client = boto3.client(
            'dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

    def list_all_tables(self):
        """全てのテーブル名を取得"""
        tables = []
        last_evaluated_table = None
        
        while True:
            if last_evaluated_table:
                response = self.client.list_tables(ExclusiveStartTableName=last_evaluated_table)
            else:
                response = self.client.list_tables()
            
            tables.extend(response.get('TableNames', []))
            
            last_evaluated_table = response.get('LastEvaluatedTableName')
            if not last_evaluated_table:
                break
                
        return tables

    def scan_table_with_retry(self, table_name, max_retries=3):
        """テーブルの全データを取得（リトライ機能付き）"""
        table = self.dynamodb.Table(table_name)
        items = []
        scan_kwargs = {
            'TableName': table_name,
            'ReturnConsumedCapacity': 'TOTAL'
        }
        
        done = False
        retries = 0
        
        while not done and retries < max_retries:
            try:
                while True:
                    response = table.scan(**scan_kwargs)
                    items.extend(response.get('Items', []))
                    
                    # レート制限に達した場合は少し待機
                    if 'ConsumedCapacity' in response:
                        capacity = response['ConsumedCapacity']['CapacityUnits']
                        if capacity > 100:  # 任意の閾値
                            time.sleep(1)
                    
                    if 'LastEvaluatedKey' not in response:
                        done = True
                        break
                        
                    scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                    
            except Exception as e:
                print(f"Error scanning table {table_name}: {str(e)}")
                retries += 1
                if retries < max_retries:
                    time.sleep(2 ** retries)  # 指数バックオフ
                else:
                    print(f"Failed to scan table {table_name} after {max_retries} attempts")
                    return []
                    
        return items

def export_all_data():
    """全てのテーブルのデータをエクスポート"""
    checker = DynamoDBChecker()
    
    # 全てのテーブルを取得
    tables = checker.list_all_tables()
    print(f"Found {len(tables)} tables: {', '.join(tables)}")
    
    # 各テーブルのデータを取得してJSONファイルに保存
    for table_name in tables:
        print(f"\nScanning table: {table_name}")
        items = checker.scan_table_with_retry(table_name)
        
        if items:
            filename = f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(items, f, indent=2, ensure_ascii=False, cls=DecimalEncoder)
            print(f"Exported {len(items)} items to {filename}")
        else:
            print(f"No items found in table {table_name}")

if __name__ == "__main__":
    export_all_data()