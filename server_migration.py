import boto3
import os
from dotenv import load_dotenv
from decimal import Decimal
import json
from datetime import datetime
import traceback
import logging

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_migration.log'),
        logging.StreamHandler()
    ]
)

class ServerPointMigration:
    def __init__(self):
        load_dotenv()
        self.dynamodb = boto3.resource('dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.users_table = self.dynamodb.Table('discord_users')
        self.target_server_ids = ['1014465423045054525', '1236319711113777233']
        
    def create_backup(self):
        """データのバックアップを作成"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f'server_backup_{timestamp}.json'
            
            # テーブルデータの取得
            response = self.users_table.scan()
            items = response['Items']
            
            # Decimal型をJSON変換可能な形式に変換
            backup_data = json.dumps(items, default=self.decimal_default, indent=2)
            
            # バックアップファイルの作成
            with open(backup_file, 'w') as f:
                f.write(backup_data)
            
            logging.info(f'バックアップを作成しました: {backup_file}')
            return True
            
        except Exception as e:
            logging.error(f'バックアップ作成中にエラーが発生しました: {str(e)}')
            logging.error(traceback.format_exc())
            return False

    def decimal_default(self, obj):
        """Decimal型をstr型に変換"""
        if isinstance(obj, Decimal):
            return str(obj)
        raise TypeError

    def get_server_records(self):
        """対象サーバーの全レコードを取得"""
        try:
            records = []
            for server_id in self.target_server_ids:
                # サーバーごとにレコードを取得
                response = self.users_table.scan(
                    FilterExpression='server_id = :sid',
                    ExpressionAttributeValues={
                        ':sid': server_id
                    }
                )
                records.extend(response['Items'])
            
            # ユーザーIDでグループ化
            user_groups = {}
            for record in records:
                user_id = record.get('user_id')
                if user_id:
                    if user_id not in user_groups:
                        user_groups[user_id] = []
                    user_groups[user_id].append(record)
            
            logging.info(f'対象ユーザー数: {len(user_groups)}')
            return user_groups
            
        except Exception as e:
            logging.error(f'レコード取得中にエラーが発生しました: {str(e)}')
            logging.error(traceback.format_exc())
            return {}

    def migrate_user_points(self, user_id, user_records):
        """個別ユーザーのポイント統合処理"""
        try:
            # サーバーごとに処理
            for server_id in self.target_server_ids:
                server_records = [r for r in user_records if r.get('server_id') == server_id]
                if not server_records:
                    continue

                # ポイントの集計
                total_points = Decimal('0')
                latest_timestamp = None
                for record in server_records:
                    if record.get('unit_id') in ['unknown', 'gacha']:
                        points = Decimal(str(record.get('points', 0)))
                        total_points += points
                        
                        # 最新のタイムスタンプを取得
                        record_timestamp = record.get('updated_at')
                        if record_timestamp and (not latest_timestamp or record_timestamp > latest_timestamp):
                            latest_timestamp = record_timestamp

                if total_points > 0:
                    # 既存のunit_id 1のレコードを確認
                    existing_records = [r for r in server_records if r.get('unit_id') == '1']
                    if existing_records:
                        existing_record = existing_records[0]
                        updated_points = existing_record.get('points', 0) + total_points
                        new_item = {
                            'user_id': user_id,
                            'server_id': server_id,
                            'unit_id': '1',
                            'points': updated_points,
                            'updated_at': latest_timestamp or datetime.now().isoformat(),
                            'pk': f'USER#{user_id}#SERVER#{server_id}#UNIT#1'
                        }
                        if 'last_gacha_date' in existing_record:
                            new_item['last_gacha_date'] = existing_record['last_gacha_date']
                    else:
                        new_item = {
                            'user_id': user_id,
                            'server_id': server_id,
                            'unit_id': '1',
                            'points': total_points,
                            'updated_at': latest_timestamp or datetime.now().isoformat(),
                            'pk': f'USER#{user_id}#SERVER#{server_id}#UNIT#1'
                        }
                        
                        # last_gacha_dateの取得（unknownまたはgachaレコードから）
                        for record in server_records:
                            if 'last_gacha_date' in record and record['last_gacha_date'] != 'unknown':
                                new_item['last_gacha_date'] = record['last_gacha_date']
                                break

                    # 新しいレコードを作成
                    logging.info(f'新しいレコードを作成します - ユーザー: {user_id}, サーバー: {server_id}')
                    self.users_table.put_item(Item=new_item)

                    # 古いレコードの削除
                    for record in server_records:
                        if record.get('unit_id') in ['unknown', 'gacha']:
                            self.users_table.delete_item(
                                Key={
                                    'pk': record['pk']
                                }
                            )
                            logging.info(f'古いレコードを削除しました - ユーザー: {user_id}, サーバー: {server_id}')

            return True

        except Exception as e:
            logging.error(f'ユーザー {user_id} のポイント統合中にエラーが発生しました: {str(e)}')
            logging.error(traceback.format_exc())
            return False

    def migrate_all_users(self):
        """全ユーザーのポイント統合処理"""
        try:
            if not self.create_backup():
                logging.error('バックアップ作成に失敗したため、処理を中止します')
                return False

            user_groups = self.get_server_records()
            if not user_groups:
                logging.error('対象レコードが見つかりませんでした')
                return False

            success_count = 0
            error_count = 0

            for user_id, user_records in user_groups.items():
                try:
                    if self.migrate_user_points(user_id, user_records):
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    logging.error(f'ユーザー {user_id} の処理中にエラーが発生しました: {str(e)}')
                    error_count += 1

            logging.info(f'処理完了 - 成功: {success_count}, 失敗: {error_count}')
            return True

        except Exception as e:
            logging.error(f'ポイント統合中にエラーが発生しました: {str(e)}')
            logging.error(traceback.format_exc())
            return False

def main():
    migration = ServerPointMigration()
    if migration.migrate_all_users():
        print('サーバー全体のポイント統合が正常に完了しました')
    else:
        print('サーバー全体のポイント統合中にエラーが発生しました')

if __name__ == "__main__":
    main()