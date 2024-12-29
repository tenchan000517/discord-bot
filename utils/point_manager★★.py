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

    async def get_points(self, server_id: str, user_id: str) -> int:
        """ユーザーのポイントを取得"""
        return await self.db.get_user_points(user_id, server_id)

    async def update_points(self, user_id: str, server_id: str, points: int, source: str = None):
        """
        ポイントを更新し、必要に応じて通知を送信
        source: ポイント変更の理由（'gacha', 'battle', 'consumption'など）
        """
        try:
            # 現在のポイントを取得
            current_points = await self.get_points(server_id, user_id)
            print(f"[DEBUG] update_points - 現在のポイント: {current_points}")

            # ポイントを更新
            success = await self.db.update_feature_points(user_id, server_id, points)
            print(f"[DEBUG] update_points - 更新成功: {success}")
            print(f"[DEBUG] update_points - 更新後のポイント: {points}")

            if success:
                # 変更量を計算
                points_change = points - current_points
                print(f"[DEBUG] update_points - ポイント変動量: {points_change}")

                if points_change > 0:
                    # ポイント獲得の通知
                    await self._notify_point_gain(server_id, user_id, points_change, source)
                elif points_change < 0:
                    # ポイント消費の通知
                    await self._notify_point_consumption(server_id, user_id, abs(points_change), source)

                # Automationマネージャーに通知
                automation_cog = self.bot.get_cog('Automation')
                if automation_cog:
                    await automation_cog.automation_manager.process_points_update(
                        user_id,
                        server_id,
                        points  # 更新後の最新のポイント
                    )

            return success

        except Exception as e:
            print(f"Error updating points: {e}")
            print(traceback.format_exc())
            return False
        
    async def _notify_point_gain(self, server_id: str, user_id: str, points: int, source: str):
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
                description=f"<@{user_id}>が{source_text}で{points}{settings.global_settings.point_unit}を獲得しました",
                color=discord.Color.green()
            )
            
            await channel.send(embed=embed)

        except Exception as e:
            print(f"Error in point gain notification: {e}")

    async def _notify_point_consumption(self, server_id: str, user_id: str, points: int, source: str):
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
                description=f"<@{user_id}>が{source}で{points}{settings.global_settings.point_unit}を消費しました",
                color=discord.Color.red()
            )
            
            await channel.send(embed=embed)

        except Exception as e:
            print(f"Error in point consumption notification: {e}")

    async def consume_points(self, server_id: str, user_id: str, points: int, reason: str = "ポイント消費") -> bool:
        """ポイントを消費する"""
        try:
            # 現在のポイントを取得
            current_points = await self.get_points(server_id, user_id)
            
            # ポイント不足チェック
            if current_points < points:
                return False

            # 新しいポイントを計算して更新
            new_points = current_points - points
            success = await self.update_points(user_id, server_id, new_points, reason)

            return success

        except Exception as e:
            print(f"Error in consume_points: {e}")
            print(traceback.format_exc())
            return False