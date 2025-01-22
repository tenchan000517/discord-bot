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
target_server_id = "1236319711113777233"

# ウォレット項目を更新する関数
def update_wallet_field():
    print("ウォレット項目の更新を開始します...")

    try:
        # 対象のサーバーIDのデータを取得
        response = table.get_item(Key={"server_id": target_server_id})
        if 'Item' not in response:
            print(f"[ERROR] 指定されたサーバーID({target_server_id})のデータが見つかりません！")
            return

        item = response['Item']

        # 該当する項目をチェック
        modal_settings = item.get('feature_settings', {}).get('point_consumption', {}).get('modal_settings', {})
        fields = modal_settings.get('fields', {})
        if fields.get('wallet') is False:
            print(f"[DEBUG] 更新対象のサーバーID: {target_server_id}")

            # wallet を True に更新
            fields['wallet'] = True

            # DynamoDBに保存
            table.put_item(Item=item)
            print(f"[INFO] サーバーID {target_server_id} の wallet を更新しました！")
        elif fields.get('wallet') is True:
            print(f"[DEBUG] サーバーID {target_server_id} の wallet は既に True です。更新不要です。")
        else:
            print(f"[WARNING] サーバーID {target_server_id} の wallet フィールドが見つかりません！")

    except Exception as e:
        print(f"[ERROR] サーバーID {target_server_id} の更新中にエラーが発生しました: {e}")

    print("ウォレット項目の更新が完了しました！")

# 実行
try:
    update_wallet_field()
except Exception as e:
    print(f"[ERROR] スクリプト実行中にエラーが発生しました: {e}")
