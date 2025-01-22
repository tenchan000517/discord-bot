import boto3
import json
from decimal import Decimal
from datetime import datetime
import pytz

# DynamoDBの設定
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table_name = "server_settings"
table = dynamodb.Table(table_name)

# 対象サーバーID
server_id = "1276791506270945322"

# バックアップを取得
def backup_table():
    print("バックアップを開始します...")
    response = table.scan()
    backup_data = response['Items']

    # バックアップデータをファイルに保存
    backup_file = f"backup_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=4, default=str)
    print(f"バックアップ完了: {backup_file}")

# データを更新
def migrate_data():
    print("マイグレーションを開始します...")

    # 現在のデータ取得
    response = table.get_item(Key={"server_id": server_id})
    if 'Item' not in response:
        print("指定されたサーバーIDのデータが見つかりません！")
        return

    item = response['Item']

    # 必要な設定を追加・更新
    item['feature_settings']['point_consumption']['modal_settings'] = {
        'title': "ポイント消費申請",
        'fields': {
            "points": True,
            "wallet": True,
            "email": False
        },
        'field_labels': {
            "points": "消費ポイント",
            "wallet": "ウォレットアドレス",
            "email": "メールアドレス"
        },
        'field_placeholders': {
            "points": "消費するポイント数を入力",
            "wallet": "0x...",
            "email": "example@example.com"
        },
        'validation': {
            "points": {"min": 0, "max": None},
            "wallet": {"pattern": "^0x[a-fA-F0-9]{40}$"},
            "email": {"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"}
        },
        'success_message': "申請を送信しました。"
    }

    # 更新処理
    table.put_item(Item=item)
    print("マイグレーションが完了しました！")

# 実行
try:
    backup_table()
    migrate_data()
except Exception as e:
    print(f"エラーが発生しました: {e}")
