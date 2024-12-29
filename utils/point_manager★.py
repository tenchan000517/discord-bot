# utils/point_manager.py
import traceback
from datetime import datetime
from typing import Dict, Optional
import pytz

class PointManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    async def get_points(self, server_id: str, user_id: str) -> int:
        """ユーザーのポイントを取得"""
        return await self.db.get_user_points(user_id, server_id)

    async def update_points(self, user_id: str, server_id: str, points: int, feature: str = None):
        """
        ポイントを更新し、Automationマネージャーに通知
        """
        try:
            # ポイントを更新
            success = await self.db.update_feature_points(
                user_id,
                server_id,
                feature if feature else 'total',
                points
            )

            if success:
                # 合計ポイントを取得
                total_points = await self.db.get_user_points(user_id, server_id)
                
                # # Automationマネージャーに通知
                # automation_cog = self.bot.get_cog('Automation')
                # if automation_cog:
                #     await automation_cog.automation_manager.process_points_update(
                #         user_id, 
                #         server_id, 
                #         total_points
                #     )

            return success

        except Exception as e:
            print(f"Error updating points: {e}")
            print(traceback.format_exc())
            return False
        
    async def consume_points(
        self,
        server_id: str,
        user_id: str,
        points: int,
        admin_id: str
    ) -> bool:
        """ポイントを消費する"""
        try:
            # 現在のポイントを取得
            current_points = await self.bot.db.get_user_points(user_id, server_id)
            print(f"消費前のポイント: {current_points}")
            print(f"消費予定のポイント: {points}")
            
            # ポイント不足チェック
            if current_points < points:
                print(f"ポイント不足: 現在 {current_points} < 必要 {points}")
                return False

            # 消費後のポイントを計算
            new_points = current_points - points
            print(f"消費後のポイント計算値: {new_points}")

            # ポイントを消費（update_pointsメソッドを使用）
            success = await self.update_points(
                user_id,
                server_id,
                new_points,
                'consumption'  # 機能名を指定
            )

            if success:
                # 更新後のポイントを確認
                final_points = await self.bot.db.get_user_points(user_id, server_id)
                print(f"消費処理後の実際のポイント: {final_points}")
                print(f"ポイント変動: {final_points - current_points}")
            else:
                print("ポイントの更新に失敗しました")

            return success

        except Exception as e:
            print(f"Error in consume_points: {e}")
            print(traceback.format_exc())
            return False

    # async def create_consumption_request(
    #     self,
    #     server_id: str,
    #     user_id: str,
    #     points: int,
    #     thread_id: Optional[str] = None
    # ) -> Optional[Dict]:
    #     """ポイント消費リクエストを作成"""
    #     try:
    #         # 現在のポイントを取得して消費可能かチェック
    #         current_points = await self.bot.db.get_user_points(user_id, server_id)
    #         if current_points < points:
    #             return None

    #         # リクエストを作成
    #         request = await self.bot.db.create_consumption_request(
    #             server_id,
    #             user_id,
    #             points,
    #             thread_id
    #         )

    #         # Automationマネージャーに通知
    #         automation_cog = self.bot.get_cog('Automation')
    #         if automation_cog and request:
    #             await automation_cog.automation_manager.process_consumption_request(
    #                 user_id,
    #                 server_id,
    #                 points,
    #                 request
    #             )

    #         return request

    #     except Exception as e:
    #         print(f"Error in create_consumption_request: {e}")
    #         print(traceback.format_exc())
    #         return None

    async def cancel_consumption_request(
        self,
        server_id: str,
        timestamp: str,
        admin_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """ポイント消費リクエストをキャンセル"""
        try:
            success = await self.bot.db.update_consumption_status(
                server_id,
                timestamp,
                'cancelled',
                admin_id,
                reason
            )

            # if success:
            #     # Automationマネージャーに通知
            #     automation_cog = self.bot.get_cog('Automation')
            #     if automation_cog:
            #         await automation_cog.automation_manager.process_consumption_cancel(
            #             server_id,
            #             timestamp,
            #             admin_id,
            #             reason
            #         )

            return success

        except Exception as e:
            print(f"Error in cancel_consumption_request: {e}")
            print(traceback.format_exc())
            return False