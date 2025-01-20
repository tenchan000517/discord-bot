import asyncio
import traceback
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Optional
import json
from decimal import Decimal

class DatabaseChecker:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.users_table = self.dynamodb.Table('discord_bot_users')  # ユーザーポイント用テーブル

    async def check_database_structure(self):
        """ユーザーポイントテーブルの構造を確認するためのヘルパー関数"""
        try:
            # テーブル構造の確認
            table_description = await asyncio.to_thread(
                self.users_table.meta.client.describe_table,
                TableName='discord_bot_users'
            )
            table_info = table_description['Table']
                
            print("\n=== ユーザーポイントテーブル構造 ===")
            print(f"テーブル名: {table_info['TableName']}")
            print(f"プライマリーキー: {json.dumps(table_info['KeySchema'], indent=2, ensure_ascii=False)}")
            print(f"属性定義: {json.dumps(table_info['AttributeDefinitions'], indent=2, ensure_ascii=False)}")
            
            if 'GlobalSecondaryIndexes' in table_info:
                print("\nGSI:")
                for gsi in table_info['GlobalSecondaryIndexes']:
                    print(f"  {gsi['IndexName']}: {json.dumps(gsi['KeySchema'], indent=2, ensure_ascii=False)}")

            # データのサンプリング
            print("\n=== データサンプル分析 ===")
            response = await asyncio.to_thread(
                self.users_table.scan,
                Limit=100  # 最初の100件のみ取得
            )
            items = response.get('Items', [])
            
            # データ構造分析
            structure_analysis = {
                'total_items': len(items),
                'unique_keys': set(),
                'pk_patterns': set(),
                'data_types': {},
                'points_structure': [],
                'unit_ids': set()
            }
            
            for item in items:
                # キーの収集
                structure_analysis['unique_keys'].update(item.keys())
                if 'pk' in item:
                    pk_parts = item['pk'].split('#')
                    structure_analysis['pk_patterns'].add(tuple(pk_parts))
                    if len(pk_parts) >= 6:  # USER#id#SERVER#id#UNIT#id の形式を想定
                        unit_id = pk_parts[5]
                        structure_analysis['unit_ids'].add(unit_id)
                
                # ポイントデータの構造を収集
                if 'points' in item:
                    points_sample = {
                        'pk': item.get('pk', ''),
                        'points': str(item['points']),
                        'type': type(item['points']).__name__
                    }
                    structure_analysis['points_structure'].append(points_sample)
                
                # データ型の分析
                for key, value in item.items():
                    if key not in structure_analysis['data_types']:
                        structure_analysis['data_types'][key] = set()
                    structure_analysis['data_types'][key].add(type(value).__name__)
            
            print(f"\n総レコード数: {structure_analysis['total_items']}")
            print(f"\nユニークなキー: {sorted(structure_analysis['unique_keys'])}")
            
            print("\nプライマリキーのパターン:")
            for pattern in structure_analysis['pk_patterns']:
                print(f"  {' -> '.join(pattern)}")
            
            print("\nユニットID一覧:", sorted(structure_analysis['unit_ids']))
            
            print("\nフィールド別データ型:")
            for key, types in sorted(structure_analysis['data_types'].items()):
                print(f"{key}: {sorted(types)}")
            
            print("\nポイントデータのサンプル（最大5件）:")
            for points_data in structure_analysis['points_structure'][:5]:
                print(json.dumps(points_data, indent=2, ensure_ascii=False))
            
            return structure_analysis
            
        except Exception as e:
            print(f"Error analyzing database structure: {e}")
            print(traceback.format_exc())
            return None

# スクリプト実行部分
async def main():
    checker = DatabaseChecker()
    await checker.check_database_structure()

if __name__ == "__main__":
    asyncio.run(main())