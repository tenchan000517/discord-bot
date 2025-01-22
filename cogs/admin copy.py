import discord
from discord import app_commands
from discord.ext import commands
import traceback

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="setup_consumption",
        description="ポイント消費パネルを設置します"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_consumption(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        """ポイント消費パネルのセットアップを行います"""
        try:

            # 直接チャンネルにメッセージを送信
            print("[DEBUG] Starting setup_consumption_panel setup...")
            
            # サーバー設定の取得
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            if not settings or not settings.point_consumption_settings:
                await interaction.response.send_message(
                    "サーバーの設定が見つかりません。",
                    ephemeral=True
                )
                return

            # PointsConsumption Cogの存在確認
            point_consumption_cog = self.bot.get_cog('PointsConsumption')
            if not point_consumption_cog:
                await interaction.response.send_message(
                    "ポイント消費機能が利用できません。",
                    ephemeral=True
                )
                return

            # パネルのセットアップ
            await point_consumption_cog.setup_consumption_panel(
                str(channel.id),
                settings
            )

            # 成功メッセージの送信
            await interaction.response.send_message(
                f"✅ ポイント消費パネルを {channel.mention} に設置しました。",
                ephemeral=True
            )

        except Exception as e:
            # エラーログの出力
            print(f"[ERROR] Error in setup_consumption: {e}")
            print(traceback.format_exc())
            
            # エラーメッセージの送信
            await interaction.response.send_message(
                "⚠️ パネルの設置中にエラーが発生しました。",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Admin(bot))