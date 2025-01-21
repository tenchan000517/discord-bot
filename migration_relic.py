import boto3
import json
from datetime import datetime
import os
import asyncio
from typing import List, Dict, Any
from decimal import Decimal

# 定数
TARGET_SERVER_ID = "1063339767653208194"
DEFAULT_UNIT_ID = "1"
BACKUP_DIR = "backups"

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # 必要に応じて float(obj) に変更可能
        return super(DecimalEncoder, self).default(obj)

class PointSystemMigration:
    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.table = self.dynamodb.Table(table_name)

    def _ensure_backup_dir(self) -> None:
        """バックアップディレクトリの確認と作成"""
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            print(f"Created backup directory: {BACKUP_DIR}")

    async def backup_data(self) -> str:
        """データのバックアップを取る"""
        try:
            self._ensure_backup_dir()
            
            # 全データの取得
            response = self.table.scan()
            items = response['Items']
            
            # 追加のページがある場合は取得
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response['Items'])

            # バックアップファイル名の生成
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(BACKUP_DIR, f'points_backup_{timestamp}.json')
            
            # バックアップの保存 (DecimalEncoder を使用)
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
            
            print(f"Backup completed: {backup_file}")
            print(f"Total items backed up: {len(items)}")
            
            return backup_file
            
        except Exception as e:
            print(f"Error during backup: {e}")
            raise

    async def migrate_data(self, backup_file: str) -> None:
        """データのマイグレーション実行"""
        try:
            # 対象サーバーのデータを取得
            response = self.table.scan(
                FilterExpression='contains(pk, :server_id)',
                ExpressionAttributeValues={':server_id': f'SERVER#{TARGET_SERVER_ID}'}
            )
            items = response['Items']
            
            # 追加のページがある場合は取得
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey'],
                    FilterExpression='contains(pk, :server_id)',
                    ExpressionAttributeValues={':server_id': f'SERVER#{TARGET_SERVER_ID}'}
                )
                items.extend(response['Items'])

            print(f"Found {len(items)} items to migrate")

            # マイグレーション処理
            updated_count = 0
            skipped_count = 0
            error_count = 0

            for item in items:
                try:
                    # UNITを含まないPKのみを処理
                    if 'UNIT#' not in item['pk']:
                        old_pk = item['pk']
                        user_id = old_pk.split('#')[1]
                        
                        # 新しいPKの生成
                        new_pk = f"USER#{user_id}#SERVER#{TARGET_SERVER_ID}#UNIT#{DEFAULT_UNIT_ID}"
                        
                        # アイテムの更新
                        updated_item = {
                            **item,
                            'pk': new_pk,
                        }
                        self.table.put_item(Item=updated_item)
                        
                        # 古いアイテムの削除
                        self.table.delete_item(
                            Key={
                                'pk': old_pk
                            }
                        )
                        
                        print(f"Migrated: {old_pk} -> {new_pk}")
                        updated_count += 1
                    else:
                        skipped_count += 1
                        print(f"Skipped (already has UNIT): {item['pk']}")
                        
                except Exception as e:
                    print(f"Error migrating item {item['pk']}: {e}")
                    error_count += 1

            print("\nMigration Summary:")
            print(f"Total items processed: {len(items)}")
            print(f"Successfully updated: {updated_count}")
            print(f"Skipped (already had UNIT): {skipped_count}")
            print(f"Errors: {error_count}")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            raise

async def run_migration(table_name: str):
    """マイグレーションの実行"""
    migrator = PointSystemMigration(table_name)
    
    # 確認プロンプト
    print(f"WARNING: This will migrate point data for server {TARGET_SERVER_ID}")
    print("Make sure you have reviewed the code and are ready to proceed.")
    confirm = input("Type 'YES' to continue: ")
    
    if confirm != "YES":
        print("Migration cancelled.")
        return
    
    try:
        # バックアップの作成
        print("\nStep 1: Creating backup...")
        backup_file = await migrator.backup_data()
        
        # 確認プロンプト
        print("\nBackup created successfully.")
        confirm = input("Type 'MIGRATE' to proceed with migration: ")
        
        if confirm != "MIGRATE":
            print("Migration cancelled.")
            return
        
        # マイグレーションの実行
        print("\nStep 2: Performing migration...")
        await migrator.migrate_data(backup_file)
        
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"\nError during migration process: {e}")
        print("Please check the backup file and database state.")

if __name__ == "__main__":
    TABLE_NAME = "discord_users"  # DynamoDBのテーブル名を指定
    
    asyncio.run(run_migration(TABLE_NAME))
