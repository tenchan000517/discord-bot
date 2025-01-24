# utils/point_manager.py
import traceback
from datetime import datetime
from typing import Dict, Optional
import pytz
import discord

class PointSource:
    GACHA = 'gacha'
    BATTLE = 'battle'
    BATTLE_WIN = 'battle_win'
    BATTLE_KILL = 'battle_kill'
    CONSUMPTION = 'consumption'

class PointManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    async def get_points(self, server_id: str, user_id: str, unit_id: str = "1") -> int:
        """
        指定されたユーザーの保有ポイントを取得する

        Args:
            server_id (str): サーバーのDiscord ID
            user_id (str): ユーザーのDiscord ID
            unit_id (str, optional): ポイントユニットのID. デフォルトは "1"

        Returns:
            int: ユーザーの保有ポイント。データが存在しない場合は0
        """
        try:
            print(f"[DEBUG] Getting points for:")
            print(f"  Server ID: {server_id}")
            print(f"  User ID: {user_id}")
            print(f"  Unit ID: {unit_id}")
            
            # ユーザーデータの取得
            data = await self.db.get_user_data(user_id, server_id, unit_id)
            print(f"[DEBUG] Retrieved user data: {data}")
            
            if not data:
                print("[DEBUG] No data found for user")
                return 0
                
            if 'points' not in data:
                print("[DEBUG] No points field in data")
                return 0
            
            # ポイントの取得と変換
            points_data = data['points']
            print(f"[DEBUG] Points data type: {type(points_data)}")
            
            try:
                # pointsが辞書型の場合の処理
                if isinstance(points_data, dict):
                    points = int(points_data.get(unit_id, 0))
                    print(f"[DEBUG] Retrieved points from dict: {points}")
                    return points
                
                # 従来の単一値の場合
                points = int(points_data)
                print(f"[DEBUG] Retrieved points as single value: {points}")
                return points
                
            except (ValueError, TypeError) as e:
                print(f"[ERROR] Error converting points value: {e}")
                return 0
                
        except Exception as e:
            print(f"[ERROR] Error in get_points: {e}")
            print(traceback.format_exc())
            return 0

    async def update_points(
        self, 
        user_id: str, 
        server_id: str, 
        points: int, 
        unit_id: str = "1", 
        source: str = None,
        wallet_address: str = None,
        username: str = None  # 新たに受け取る
    ) -> bool:
        """
        ポイントを増減させる（増加は正の値、減少は負の値）

        Args:
            user_id (str): ユーザーID
            server_id (str): サーバーID
            points (int): 増減させるポイント量（正の値で増加、負の値で減少）
            unit_id (str, optional): ポイントユニットID. デフォルトは "1"
            source (str, optional): ポイント変動の発生元（例: 承認者のユーザーID）
            wallet_address (str, optional): ユーザーのウォレットアドレス. デフォルトは None

        Returns:
            bool: 操作が成功したかどうか

        Raises:
            Exception: 処理中に予期しないエラーが発生した場合
        """
        try:
            # 現在のポイントを取得
            current_points = await self.get_points(server_id, user_id, unit_id)
            
            # 新しい合計を計算
            new_total = current_points + points
            
            # マイナスにならないようにチェック
            if new_total < 0:
                return False
                
            # ポイントを更新 (ウォレットアドレスを含めて保存)
            success = await self.db.update_feature_points(
                user_id=user_id, 
                server_id=server_id, 
                points=new_total, 
                unit_id=unit_id,
                wallet_address=wallet_address,
                username=username  # 渡す
            )            
            if success:

                # サーバー設定を取得してポイント単位名を決定
                settings = await self.bot.get_server_settings(server_id)
                point_unit_name = settings.global_settings.point_unit
                if settings.global_settings.multiple_points_enabled:
                    point_unit = next(
                        (unit for unit in settings.global_settings.point_units 
                        if unit.unit_id == unit_id),
                        None
                    )
                    if point_unit:
                        point_unit_name = point_unit.name

                # 通知処理
                if points > 0:
                    await self._notify_point_gain(server_id, user_id, points, source, unit_id, point_unit_name)
                elif points < 0:
                    await self._notify_point_consumption(server_id, user_id, abs(points), source, unit_id, point_unit_name)

                # Automationマネージャーに通知
                automation_cog = self.bot.get_cog('Automation')
                if automation_cog:
                    await automation_cog.automation_manager.process_points_update(
                        user_id, server_id, new_total, unit_id
                    )

            return success

        except Exception as e:
            print(f"Error updating points: {e}")
            print(traceback.format_exc())
            return False

    async def _notify_point_gain(self, server_id: str, user_id: str, points: int, 
                               source: str, unit_id: str, unit_name: str):
        """ポイント獲得の通知"""
        try:
            settings = await self.bot.get_server_settings(server_id)
            if not settings or not settings.point_consumption_settings.gain_history_enabled:
                return

            channel_id = settings.point_consumption_settings.gain_history_channel_id
            if not channel_id:
                return

            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return

            source_text = {
                'gacha': 'ガチャ',
                'battle': 'バトル',
                'battle_win': 'バトル優勝',
                'battle_kill': 'バトルキル報酬',
            }.get(source, source)

            embed = discord.Embed(
                title="ポイント獲得",
                description=f"<@{user_id}>が{source_text}で{points}{unit_name}を獲得しました",
                color=discord.Color.green()
            )
            
            await channel.send(embed=embed)

        except Exception as e:
            print(f"Error in point gain notification: {e}")

    async def _notify_point_consumption(self, server_id: str, user_id: str, points: int, 
                                      source: str, unit_id: str, unit_name: str):
        """ポイント消費の通知"""
        try:
            settings = await self.bot.get_server_settings(server_id)
            if not settings or not settings.point_consumption_settings.consumption_history_enabled:
                return

            channel_id = settings.point_consumption_settings.consumption_history_channel_id
            if not channel_id:
                return

            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return

            embed = discord.Embed(
                title="ポイント消費",
                description=f"<@{user_id}>が{source}で{points}{unit_name}を消費しました",
                color=discord.Color.red()
            )
            
            await channel.send(embed=embed)

        except Exception as e:
            print(f"Error in point consumption notification: {e}")

    async def consume_points(
        self, 
        server_id: str, 
        user_id: str, 
        points: int, 
        reason: str = "ポイント消費", 
        unit_id: str = "1", 
        source: str = None, 
        wallet_address: str = None
    ) -> bool:
        """
        ポイントを消費する

        Args:
            server_id (str): サーバーID
            user_id (str): ユーザーID
            points (int): 消費するポイント量（正の整数値）
            reason (str, optional): 消費理由. デフォルトは "ポイント消費"
            unit_id (str, optional): ポイントユニットID. デフォルトは "1"
            source (str, optional): ポイント変動の発生元（例: 承認者のユーザーID）. デフォルトは None
            wallet_address (str, optional): ユーザーのウォレットアドレス. デフォルトは None

        Returns:
            bool: 操作が成功したかどうか

        Raises:
            Exception: 処理中に予期しないエラーが発生した場合
        """
        try:
            # 現在のポイントを取得
            current_points = await self.get_points(server_id, user_id, unit_id)

            # ポイント不足チェック
            if current_points < points:
                print(f"[DEBUG] User {user_id} has insufficient points. Required: {points}, Available: {current_points}")
                return False

            # 新しいポイントを計算
            new_points = current_points - points

            # ポイントの更新
            success = await self.update_points(
                user_id=user_id, 
                server_id=server_id, 
                points=-points,  # ここをマイナスに
                unit_id=unit_id, 
                source=source, 
                wallet_address=wallet_address  # ウォレットアドレスを追加
            )

            if not success:
                print(f"[DEBUG] Failed to update points for user {user_id} in server {server_id}")
                return False

            # ログ出力（デバッグ用）
            print(f"[INFO] Points successfully consumed for user {user_id} in server {server_id}.")
            print(f"  - Points consumed: {points}")
            print(f"  - New balance: {new_points}")
            print(f"  - Unit ID: {unit_id}")
            print(f"  - Source: {source}")
            if wallet_address:
                print(f"  - Wallet Address: {wallet_address}")

            return True

        except Exception as e:
            print(f"[ERROR] Error in consume_points: {e}")
            print(traceback.format_exc())
            return False
