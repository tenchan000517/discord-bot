import boto3
from datetime import datetime
import os
import pytz
from boto3.dynamodb.conditions import Key
from typing import Optional, Dict, List, Union
import asyncio
import traceback
from decimal import Decimal
import uuid

class AWSDatabase:
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.users_table = self.dynamodb.Table('discord_users')
        self.settings_table = self.dynamodb.Table('server_settings')
        # self.history_table = self.dynamodb.Table('gacha_history')

        self.automation_rules_table = self.dynamodb.Table('automation_rules')
        # self.automation_history_table = self.dynamodb.Table('automation_history')

        self.point_consumption_history_table = self.dynamodb.Table('point_consumption_history')

    async def get_server_settings(self, server_id: str) -> Optional[Dict]:
        """
        DynamoDBからサーバー設定を取得する
        
        Args:
            server_id (str): サーバーID
            
        Returns:
            Optional[Dict]: 設定データ。存在しない場合はNone

        呼び出し元
        utils\settings_manager.py
        get_settings
        
        """
        try:
            response = await asyncio.to_thread(
                self.settings_table.get_item,
                Key={'server_id': str(server_id)}
            )
            return response.get('Item')  # 存在しない場合はNoneを返す
            
        except Exception as e:
            print(f"Error getting server settings: {e}")
            return None
        
    # ３番目に呼び出される serversettings_managerのcreate_default_settingsから呼び出される
    async def update_server_settings(self, server_id: str, settings: Dict) -> bool:
        """サーバー設定を非同期で更新"""
        try:
            # print(f"[DEBUG] Received settings in update_server_settings: {settings}")
            # print(f"[DEBUG] Type of settings in update_server_settings: {type(settings)}")

            # 必要なフィールドの補完
            settings['server_id'] = str(server_id)
            settings['updated_at'] = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
            if 'version' not in settings:
                settings['version'] = 1

            # DynamoDB の非同期操作
            await asyncio.to_thread(
                self.settings_table.put_item,
                Item=settings
            )
            return True
        except Exception as e:
            print(f"Error updating server settings: {e}")
            return False

    async def get_server_user_rankings(self, server_id: str) -> List[Dict]:
        """
        サーバー内のユーザーランキングを取得
        UNITごとの異なるポイントプールに対応

        主な呼び出し元:
        - cogs/gacha.py:
            - GachaView.check_points(): 
            ユーザーのガチャポイントとランキングを表示する際に使用
            特定のUNIT_IDに対応するランキングをフィルタリングして使用

        引数:
            server_id: str - ランキングを取得するサーバーのID

        戻り値:
            List[Dict] - 以下の形式のディクショナリのリスト:
            [
                {
                    'user_id': str,
                    'unit_id': str,
                    'points': int
                },
                ...
            ]
        """
        try:
            response = await asyncio.to_thread(
                self.users_table.scan
            )
            
            server_rankings = []
            for item in response.get('Items', []):
                pk = item.get('pk', '')
                if f'SERVER#{server_id}' in pk:
                    # PKから情報を抽出
                    pk_parts = pk.split('#')
                    user_id = pk_parts[1]
                    unit_id = pk_parts[5] if len(pk_parts) > 5 else '1'
                    
                    try:
                        points = int(float(item.get('points', 0)))
                    except (ValueError, TypeError):
                        print(f"[DEBUG] Invalid points value for {pk}")
                        points = 0
                    
                    server_rankings.append({
                        'user_id': user_id,
                        'unit_id': unit_id,
                        'points': points
                    })
            
            # ポイントで降順ソート（unit_idごとに別のランキングとして扱う）
            server_rankings.sort(key=lambda x: (x['unit_id'], -x['points']))
            
            print(f"[DEBUG] サーバー {server_id} のランキングデータ数: {len(server_rankings)}")
            return server_rankings
                    
        except Exception as e:
            print(f"Error getting server rankings: {str(e)}")
            print(traceback.format_exc())
            return []

    async def update_user_points(self, user_id: str, server_id: str, points: int, unit_id: str = "1") -> bool:
        """
        既存メソッドを新しい構造に対応させる
        
        呼び出し元
        utils\automation_manager.py
        process_points_update
            _execute_actions
                _execute_single_action

        """
        try:
            return await self.update_feature_points(
                user_id, 
                server_id, 
                points,
                unit_id
            )
        except Exception as e:
            print(f"Error in update_user_points: {e}")
            return False

    async def update_feature_points(self, user_id: str, server_id: str, points: int, unit_id: str = "1") -> bool:
        """
        ユーザーのポイントを更新する

        Args:
            user_id (str): ユーザーのDiscord ID
            server_id (str): サーバーのDiscord ID
            points (int): 更新後の最終的なポイント値
            unit_id (str, optional): ポイントユニットのID. デフォルトは "1"

        Returns:
            bool: 更新が成功したかどうか

        Note:
            - pointsパラメータには更新後の最終的なポイント値を渡すこと
            - 例:現在のポイントが100で、50ポイント消費する場合は、points=50を渡す
            - 新規ユーザーの場合は新しいレコードを作成
            - 既存ユーザーの場合は指定されたポイント値で更新

        self
        update_user_points

        utils\point_manager.py
        update_points

        """
        try:
            # パーティションキーを生成
            pk = self._create_pk(user_id, server_id, unit_id)
            
            # 現在のユーザーデータを取得
            current_data = await self.get_user_data(user_id, server_id, unit_id)
            
            if not current_data:
                # 新規ユーザーの場合、新しいレコードを作成
                current_data = {
                    'pk': pk,
                    'user_id': str(user_id),
                    'server_id': str(server_id),
                    'unit_id': unit_id,
                    'points': Decimal(str(points)),
                    'created_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat(),
                    'updated_at': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
                }
            else:
                # 既存ユーザーの場合、ポイントと更新日時を更新
                current_data['points'] = Decimal(str(points))
                current_data['updated_at'] = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()

            # DynamoDBにデータを保存
            await asyncio.to_thread(
                self.users_table.put_item,
                Item=current_data
            )
            
            print(f"[DEBUG] Successfully updated points for user {user_id} to {points}")
            return True
            
        except Exception as e:
            print(f"Error updating points: {e}")
            print(traceback.format_exc())
            return False

    def _create_pk(self, user_id: str, server_id: str, unit_id: str = "1") -> str:
        """
        ユーザーデータ用のプライマリキーを生成する

        Args:
            user_id (str): ユーザーのDiscord ID
            server_id (str): サーバーのDiscord ID
            unit_id (str, optional): ポイントユニットのID. デフォルトは "1"

        Returns:
            str: 生成されたプライマリキー (形式: USER#{user_id}#SERVER#{server_id}#UNIT#{unit_id})

        Raises:
            ValueError: パラメータが無効な場合（空文字列や不適切な型）
        """
        try:
            # パラメータの検証
            if not all(isinstance(x, str) for x in [user_id, server_id, unit_id]):
                raise ValueError("All parameters must be strings")
            
            if not all(x.strip() for x in [user_id, server_id, unit_id]):
                raise ValueError("All parameters must be non-empty strings")

            # プライマリキーの生成
            pk = f"USER#{user_id}#SERVER#{server_id}#UNIT#{unit_id}"
            print(f"[DEBUG] Generated PK: {pk}")
            return pk

        except Exception as e:
            print(f"[ERROR] Error in _create_pk: {e}")
            raise

    async def get_user_data(self, user_id: str, server_id: str, unit_id: str = "1") -> Optional[Dict]:
        """
        指定されたユーザー、サーバー、ユニットIDに対応するデータを取得する

        Args:
            user_id (str): ユーザーのDiscord ID
            server_id (str): サーバーのDiscord ID
            unit_id (str, optional): ポイントユニットのID. デフォルトは "1"

        Returns:
            Optional[Dict]: ユーザーデータを含む辞書。データが存在しない場合はNone

        Raises:
            Exception: データベースアクセスに失敗した場合

        呼び出し元
        self
        update_feature_points

        utils\point_manager.py
        get_points
        
        """
        try:
            print(f"[DEBUG] Getting user data for:")
            print(f"  user_id: {user_id}")
            print(f"  server_id: {server_id}")
            print(f"  unit_id: {unit_id}")

            # プライマリキーの生成
            pk = self._create_pk(user_id, server_id, unit_id)
            print(f"[DEBUG] Using PK for query: {pk}")
            print(f"[DEBUG] PK exact length: {len(pk)}")
            print(f"[DEBUG] PK character codes: {[ord(c) for c in pk]}")  # 不可視文字のチェック

            # DynamoDBからデータ取得
            response = await asyncio.to_thread(
                self.users_table.get_item,
                Key={'pk': pk}
            )
            print(f"[DEBUG] DynamoDB response: {response}")

            return response.get('Item')

        except Exception as e:
            print(f"[ERROR] Error in get_user_data: {e}")
            print(traceback.format_exc())
            return None

        
    async def get_automation_rules(self, server_id: str) -> List[Dict]:
        """
        
        サーバーのオートメーションルールを非同期で取得
        
        呼び出し元
        utils\automation_manager.py
        get_server_rules

        create_rule
        update_rule
        
        """
        try:
            response = await asyncio.to_thread(
                self.automation_rules_table.query,
                KeyConditionExpression=Key('server_id').eq(str(server_id))
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting automation rules: {e}")
            return []

    async def save_automation_rule(self, rule_data: dict) -> bool:
        """オートメーションルールを非同期で保存"""
        try:
            await asyncio.to_thread(
                self.automation_rules_table.put_item,
                Item=rule_data
            )
            return True
        except Exception as e:
            print(f"Error saving automation rule: {e}")
            return False


        
    async def save_consumption_history(self, history_data: dict) -> bool:
        """
        
        消費履歴をデータベースに保存
        
        呼び出し元

        cogs\points_consumption.py
            create_consumption_request

        cogs\points_consumption.py
            class PointConsumptionModal
                on_submit

        """
        try:
            timestamp = datetime.now(pytz.UTC).isoformat()
            item = {
                'server_id': history_data['server_id'],
                'timestamp': timestamp,
                'user_id': history_data['user_id'],
                'points': history_data['points'],
                'wallet_address': history_data.get('wallet_address'),
                'email': history_data.get('email'),
                'status': history_data.get('status', 'pending'),
                'created_at': timestamp,
                'updated_at': timestamp,
                'thread_id': history_data.get('thread_id'),
                'unit_id': history_data.get('unit_id')  # unit_idを追加
            }
            await asyncio.to_thread(
                self.point_consumption_history_table.put_item,
                Item=item
            )
            return True
        except Exception as e:
            print(f"Error saving consumption history: {e}")
            return False
  
    async def update_consumption_status(
        self,
        server_id: str,
        timestamp: str,
        status: str,
        admin_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        
        消費リクエストのステータスを更新
        
        呼び出し元
        point_comsumption.py
            handle_approve_button
        
        """
        try:
            update_expression = "SET #s = :status, admin_id = :admin_id, updated_at = :time"
            expression_names = {
                '#s': 'status'  # status は予約語なので # を使用
            }
            expression_values = {
                ':status': status,
                ':admin_id': admin_id,
                ':time': datetime.now(pytz.UTC).isoformat()
            }

            if reason:
                update_expression += ", status_reason = :reason"
                expression_values[':reason'] = reason

            print(f"[DEBUG] Updating DynamoDB with expression: {update_expression}")
            print(f"[DEBUG] Expression names: {expression_names}")
            print(f"[DEBUG] Expression values: {expression_values}")

            await asyncio.to_thread(
                self.point_consumption_history_table.update_item,
                Key={
                    'server_id': str(server_id),
                    'timestamp': timestamp
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values
            )

            # 更新後の値を確認するためのログ
            result = await asyncio.to_thread(
                self.point_consumption_history_table.get_item,
                Key={
                    'server_id': str(server_id),
                    'timestamp': timestamp
                }
            )
            print(f"[DEBUG] Updated item: {result.get('Item')}")


            return True
        except Exception as e:
            print(f"Error updating consumption status: {e}")
            print(traceback.format_exc())  # スタックトレースを出力
            return False

    # bot招待後一番最初に仕事をする→settings_managerのcreate_default_settingsへ
    async def register_server(self, server_id: str):
        """サーバーがDB上に存在するかどうかをチェックする関数"""
        try:
            # 既存の設定を確認
            response = await asyncio.to_thread(
                self.settings_table.get_item,
                Key={'server_id': str(server_id)}
            )
            
            # 存在チェックの結果を返す
            exists = 'Item' in response
            return exists

        except Exception as e:
            print(f"Error checking server {server_id}: {e}")
            raise

    async def remove_server(self, server_id: str):
        """サーバーIDをserver_settingsテーブルから削除"""
        try:
            await asyncio.to_thread(
                self.settings_table.delete_item,
                Key={'server_id': str(server_id)}
            )
            return True
        except Exception as e:
            print(f"Error removing server {server_id}: {e}")
            raise

    async def register_existing_servers(self, guilds):
        """既存のサーバーを一括登録"""
        for guild in guilds:
            try:
                await self.register_server(str(guild.id))
                print(f"Registered existing server: {guild.name} (ID: {guild.id})")
            except Exception as e:
                print(f"Error registering existing server {guild.id}: {e}")

    # 未実装
    async def save_reward(self, reward_data: dict) -> bool:
        """報酬データを保存"""
        try:
            await asyncio.to_thread(
                self.reward_claims_table.put_item,
                Item=reward_data
            )
            return True
        except Exception as e:
            print(f"Error saving reward: {e}")
            return False

    async def get_user_rewards(
        self,
        user_id: str,
        server_id: str,
        status: Optional[str] = None
    ) -> List[Dict]:
        """ユーザーの報酬履歴を取得"""
        try:
            # クエリ条件の構築
            key_condition = Key('user_id').eq(str(user_id))
            filter_expression = None

            if status:
                filter_expression = Attr('status').eq(status)
                if server_id:
                    filter_expression = filter_expression & Attr('server_id').eq(str(server_id))
            elif server_id:
                filter_expression = Attr('server_id').eq(str(server_id))

            # クエリの実行
            kwargs = {
                'KeyConditionExpression': key_condition,
                'ScanIndexForward': False  # 新しい順
            }
            if filter_expression:
                kwargs['FilterExpression'] = filter_expression

            response = await asyncio.to_thread(
                self.reward_claims_table.query,
                **kwargs
            )
            return response.get('Items', [])

        except Exception as e:
            print(f"Error getting user rewards: {e}")
            return []
        
    async def get_rewards_by_status(
        self,
        status: str,
        server_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """ステータスごとの報酬履歴を取得"""
        try:
            kwargs = {
                'IndexName': 'StatusIndex',
                'KeyConditionExpression': Key('status').eq(status),
                'Limit': limit,
                'ScanIndexForward': False
            }

            if server_id:
                kwargs['FilterExpression'] = Attr('server_id').eq(str(server_id))

            response = await asyncio.to_thread(
                self.reward_claims_table.query,
                **kwargs
            )
            return response.get('Items', [])

        except Exception as e:
            print(f"Error getting rewards by status: {e}")
            return []
        
    # インスタンス初期化時にテーブル参照を追加
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name='ap-northeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        # 既存のテーブル参照
        self.users_table = self.dynamodb.Table('discord_users')
        self.settings_table = self.dynamodb.Table('server_settings')
        self.history_table = self.dynamodb.Table('gacha_history')
        self.automation_rules_table = self.dynamodb.Table('automation_rules')
        # 新規テーブル参照を追加
        self.point_consumption_history_table = self.dynamodb.Table('point_consumption_history')