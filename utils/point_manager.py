# utils/point_manager.py として新規作成

class PointManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

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
                
                # Automationマネージャーに通知
                automation_cog = self.bot.get_cog('Automation')
                if automation_cog:
                    await automation_cog.automation_manager.process_points_update(
                        user_id, 
                        server_id, 
                        total_points
                    )

            return success

        except Exception as e:
            print(f"Error updating points: {e}")
            print(traceback.format_exc())
            return False