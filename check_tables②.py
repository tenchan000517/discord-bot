import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def list_tables_detailed():
    try:
        dynamodb = boto3.resource(
            'dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # DynamoDBクライアント
        dynamodb_client = dynamodb.meta.client

        # テーブル一覧を取得
        tables = list(dynamodb.tables.all())
        print("\n=== DynamoDB テーブル一覧 ===")
        for table in tables:
            print(f"テーブル名: {table.name}")
            # テーブルの詳細情報を取得
            table_detail = dynamodb_client.describe_table(TableName=table.name)
            
            # 基本情報の表示
            table_info = table_detail['Table']
            print(f"ステータス: {table_info['TableStatus']}")
            print("作成日時:", table_info['CreationDateTime'])
            print(f"プロビジョニングされたスループット:")
            print(f"  - 読み込みキャパシティ単位: {table_info['ProvisionedThroughput']['ReadCapacityUnits']}")
            print(f"  - 書き込みキャパシティ単位: {table_info['ProvisionedThroughput']['WriteCapacityUnits']}")
            
            # キースキーマの表示
            print("キースキーマ:")
            for key in table_info['KeySchema']:
                print(f"  - {key['AttributeName']} ({key['KeyType']})")

            print("テーブルの中身:")
            try:
                # データをスキャンして取得
                response = table.scan()
                items = response.get('Items', [])
                if not items:
                    print("  データなし")
                else:
                    for i, item in enumerate(items, start=1):
                        print(f"  データ {i}: {item}")
            except Exception as e:
                print(f"  データ取得中にエラーが発生: {e}")

            # 属性定義の表示
            print("属性定義:")
            for attr in table_info['AttributeDefinitions']:
                print(f"  - {attr['AttributeName']} ({attr['AttributeType']})")

            # インデックス情報の表示
            global_indexes = table_info.get('GlobalSecondaryIndexes', [])
            if global_indexes:
                print("グローバルセカンダリインデックス:")
                for gsi in global_indexes:
                    print(f"  - インデックス名: {gsi['IndexName']}")
                    print(f"    キースキーマ:")
                    for key in gsi['KeySchema']:
                        print(f"      - {key['AttributeName']} ({key['KeyType']})")
                    print(f"    読み込みキャパシティ: {gsi['ProvisionedThroughput']['ReadCapacityUnits']}")
                    print(f"    書き込みキャパシティ: {gsi['ProvisionedThroughput']['WriteCapacityUnits']}")

            print("-" * 50)

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    list_tables_detailed()
