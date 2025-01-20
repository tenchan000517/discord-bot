import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
from decimal import Decimal
from datetime import datetime
import os
from collections import defaultdict

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

class PointsMigration:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.users_table = self.dynamodb.Table('discord_users')
        self.target_servers = ['1236319711113777233', '1014465423045054525']
        self.backup_dir = 'dynamodb_backup'

    def extract_record_info(self, record):
        """レコードから必要な情報を抽出"""
        try:
            server_id = record.get('server_id')
            user_id = record.get('user_id')
            unit_id = record.get('unit_id', '1')
            if unit_id == 'N/A':
                unit_id = '1'
            points = Decimal(str(record.get('points', 0)))
            
            # server_idとuser_idが存在し、数値形式であることを確認
            if (server_id and user_id and 
                server_id.isdigit() and 
                user_id.isdigit() and 
                server_id in self.target_servers):
                return {
                    'server_id': server_id,
                    'user_id': user_id,
                    'unit_id': unit_id,
                    'points': points
                }
        except Exception as e:
            print(f"データ抽出エラー: {str(e)}, record: {record}")
        return None

    def is_valid_pk(self, pk, server_id):
        """PKの形式を検証"""
        parts = pk.split('#')
        try:
            if len(parts) not in [4, 6]:
                return False
            if parts[0] != 'USER' or parts[2] != 'SERVER':
                return False
            if parts[3] != server_id or not parts[3].isdigit():
                return False
            if len(parts) == 6:
                if parts[4] != 'UNIT' or not parts[5].isdigit():
                    return False
            return True
        except Exception:
            return False

    def create_backup(self):
        """バックアップ作成"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_data = []

        for server_id in self.target_servers:
            response = self.users_table.scan(
                FilterExpression=Attr('server_id').eq(server_id)
            )
            backup_data.extend(response['Items'])

        backup_file = f'{self.backup_dir}/backup_{timestamp}.json'
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, cls=DecimalEncoder, indent=2)
        
        print(f"バックアップを作成しました: {backup_file}")
        return backup_file

    def analyze_data(self):
        """データの分析とグループ化"""
        # サーバーID -> ユーザーID -> ユニットID -> ポイント
        point_totals = defaultdict(lambda: defaultdict(lambda: defaultdict(Decimal)))
        records_to_delete = []

        for server_id in self.target_servers:
            response = self.users_table.scan(
                FilterExpression=Attr('server_id').eq(server_id)
            )
            items = response['Items']

            for item in items:
                record_info = self.extract_record_info(item)
                if not record_info:
                    continue

                if self.is_valid_pk(item['pk'], server_id):
                    # 有効なPKの場合
                    point_totals[server_id][record_info['user_id']][record_info['unit_id']] += record_info['points']
                    if len(item['pk'].split('#')) == 4:  # 古い形式は削除対象
                        records_to_delete.append(item)
                else:
                    # 不正なPKの場合でも、データが有効なら集計に含める
                    print(f"不正なPK {item['pk']} からデータを復元: {record_info['points']} ポイント")
                    point_totals[server_id][record_info['user_id']][record_info['unit_id']] += record_info['points']
                    records_to_delete.append(item)

        return point_totals, records_to_delete

    def generate_migration_plan(self, point_totals, records_to_delete):
        """マイグレーション計画の生成"""
        migration_plan = {
            'updates': [],
            'deletes': []
        }

        print("\n=== マイグレーション計画 ===")
        # 新しいレコードの作成計画
        for server_id in point_totals:
            print(f"\nサーバー {server_id}:")
            for user_id in point_totals[server_id]:
                for unit_id, points in point_totals[server_id][user_id].items():
                    new_pk = f"USER#{user_id}#SERVER#{server_id}#UNIT#{unit_id}"
                    print(f"作成/更新: {new_pk} - {points} ポイント")
                    
                    migration_plan['updates'].append({
                        'pk': new_pk,
                        'points': points,
                        'server_id': server_id,
                        'user_id': user_id,
                        'unit_id': unit_id
                    })

        # 削除対象のレコード
        print("\n削除対象レコード:")
        for record in records_to_delete:
            print(f"削除: {record['pk']}")
            migration_plan['deletes'].append({
                'pk': record['pk']
            })

        return migration_plan

    def execute_migration(self, migration_plan):
        """マイグレーションの実行"""
        try:
            print("\nマイグレーションを実行中...")
            
            # 更新の実行
            for update in migration_plan['updates']:
                self.users_table.put_item(Item=update)
                print(f"更新完了: {update['pk']} - {update['points']} ポイント")

            # 削除の実行
            for delete in migration_plan['deletes']:
                self.users_table.delete_item(Key={'pk': delete['pk']})
                print(f"削除完了: {delete['pk']}")

            return True
        except Exception as e:
            print(f"マイグレーション中にエラーが発生: {str(e)}")
            return False

def main():
    migration = PointsMigration()
    
    # バックアップの作成
    print("バックアップを作成中...")
    backup_file = migration.create_backup()
    print(f"バックアップ完了: {backup_file}")

    # データ分析
    print("\nデータを分析中...")
    point_totals, records_to_delete = migration.analyze_data()

    # マイグレーション計画の生成
    print("\nマイグレーション計画を生成中...")
    migration_plan = migration.generate_migration_plan(point_totals, records_to_delete)
    
    # 計画の概要を表示
    print(f"\n更新予定レコード数: {len(migration_plan['updates'])}")
    print(f"削除予定レコード数: {len(migration_plan['deletes'])}")
    
    # 確認
    confirmation = input("\nマイグレーションを実行しますか？ (yes/no): ")
    if confirmation.lower() == 'yes':
        success = migration.execute_migration(migration_plan)
        if success:
            print("\nマイグレーションが完了しました")
        else:
            print("\nマイグレーションに失敗しました")
            print("バックアップから復元することができます")
    else:
        print("\nマイグレーションをキャンセルしました")

if __name__ == "__main__":
    main()