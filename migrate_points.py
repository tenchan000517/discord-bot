import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from decimal import Decimal
import time
import json

load_dotenv()

def migrate_user_points():
    try:
        # DynamoDBクライアントの初期化
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # discord_usersテーブルの取得
        table = dynamodb.Table('discord_users')
        
        print("ユーザーポイントのマイグレーションを開始します...")
        
        # 全データのスキャン
        response = table.scan()
        migrated_count = 0
        
        for item in response['Items']:
            points = item.get('points')
            
            # 旧形式のデータを検出（オブジェクトで、totalフィールドを持つ）
            if isinstance(points, dict) and 'total' in points:
                try:
                    # 新形式に変換
                    new_points = Decimal(str(points['total']))
                    
                    # データの更新
                    update_response = table.update_item(
                        Key={
                            'pk': item['pk']
                        },
                        UpdateExpression='SET points = :points',
                        ExpressionAttributeValues={
                            ':points': new_points
                        }
                    )
                    
                    migrated_count += 1
                    print(f"Migrated {item['pk']}: {json.dumps(points)} -> {new_points}")
                    
                except Exception as update_error:
                    print(f"更新エラー {item['pk']}: {update_error}")
                    continue
        
        print(f"マイグレーション完了！ {migrated_count}件のレコードを更新しました")

    except ClientError as e:
        print(f"エラーが発生しました: {e}")
        raise e
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        raise e

def fix_specific_user():
    try:
        # DynamoDBクライアントの初期化
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        table = dynamodb.Table('discord_users')
        
        # 問題のあるユーザーのデータを修正
        user_id = "976427276340166696"
        server_id = "1014465423045054525"
        pk = f"USER#{user_id}#SERVER#{server_id}"
        
        # 現在のデータを取得して確認
        response = table.get_item(Key={'pk': pk})
        current_data = response.get('Item', {})
        print(f"現在のデータ: {current_data}")
        
        # 正しい値（30）をDecimal型で設定
        table.update_item(
            Key={'pk': pk},
            UpdateExpression='SET points = :points',
            ExpressionAttributeValues={
                ':points': Decimal('30')
            }
        )
        
        # 更新後のデータを確認
        response = table.get_item(Key={'pk': pk})
        updated_data = response.get('Item', {})
        print(f"更新後のデータ: {updated_data}")
        
        print("修正完了")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        raise e


def check_migration_results():
    try:
        # DynamoDBクライアントの初期化
        dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        table = dynamodb.Table('discord_users')
        response = table.scan()
        
        print("\nマイグレーション結果の確認:")
        print("========================")
        
        for item in response['Items']:
            points = item.get('points')
            print(f"User: {item['user_id']}")
            print(f"Points type: {type(points)}")
            print(f"Points value: {points}")
            print("------------------------")

    except Exception as e:
        print(f"確認中にエラーが発生しました: {e}")
        raise e

if __name__ == "__main__":
    # マイグレーションの実行
    migrate_user_points()
    fix_specific_user()

    # 少し待機してから結果を確認
    time.sleep(2)
    print("\nマイグレーション結果を確認します...")
    check_migration_results()