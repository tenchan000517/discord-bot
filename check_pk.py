import boto3
from pprint import pprint

def check_table_pk():
    # DynamoDBクライアントの初期化
    dynamodb = boto3.client('dynamodb')
    
    try:
        # テーブル情報を取得
        response = dynamodb.describe_table(
            TableName='point_consumption_history'
        )
        
        print("=== Table Key Schema ===")
        pprint(response['Table']['KeySchema'])
        
        print("\n=== Table Attributes ===")
        pprint(response['Table']['AttributeDefinitions'])
        
        # インデックス情報も確認
        if 'GlobalSecondaryIndexes' in response['Table']:
            print("\n=== Global Secondary Indexes ===")
            for gsi in response['Table']['GlobalSecondaryIndexes']:
                print(f"\nIndex: {gsi['IndexName']}")
                print("Key Schema:")
                pprint(gsi['KeySchema'])
        
        if 'LocalSecondaryIndexes' in response['Table']:
            print("\n=== Local Secondary Indexes ===")
            for lsi in response['Table']['LocalSecondaryIndexes']:
                print(f"\nIndex: {lsi['IndexName']}")
                print("Key Schema:")
                pprint(lsi['KeySchema'])
                
    except Exception as e:
        print(f"Error describing table: {str(e)}")

if __name__ == "__main__":
    check_table_pk()