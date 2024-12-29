import boto3
from botocore.exceptions import BotoCoreError, ClientError

def fetch_all_points_with_type(table_name):
    """
    DynamoDB テーブルの全ポイントデータを取得し、points フィールドの型を特定
    """
    try:
        # DynamoDB リソースの初期化
        dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
        table = dynamodb.Table(table_name)

        # テーブル全体をスキャン
        print(f"Scanning table '{table_name}' for all points data...")
        response = table.scan()
        items = response.get('Items', [])

        # データが存在する場合
        if items:
            print("\n=== All Points Data with Type ===")
            for item in items:
                points = item.get('points', 'No Points')
                points_type = type(points).__name__  # 型を特定
                print(f"User: {item.get('pk')}, Points: {points}, Type: {points_type}")
        else:
            print("No data found in the table.")

    except (BotoCoreError, ClientError) as error:
        print("Error fetching data from DynamoDB:", error)

# 実行
if __name__ == "__main__":
    table_name = "discord_users"  # DynamoDB テーブル名
    fetch_all_points_with_type(table_name)
