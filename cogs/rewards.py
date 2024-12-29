# cogs/rewards.py
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal
import traceback

class Rewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="claim",
        description="ポイントを報酬と交換します"
    )
    @app_commands.describe(
        reward_type="交換したい報酬の種類を選択してください",
        points="交換に使用するポイント数を入力してください"
    )
    async def claim(
        self,
        interaction: discord.Interaction,
        reward_type: Literal["coupon", "nft", "token"],
        points: int
    ):
        """報酬との交換コマンド"""
        try:
            # 入力値の検証
            if points <= 0:
                await interaction.response.send_message(
                    "ポイントは1以上を指定してください。",
                    ephemeral=True
                )
                return

            # 一時応答を送信
            await interaction.response.defer(ephemeral=True)

            # 報酬の請求
            reward = await self.bot.reward_manager.claim_reward(
                str(interaction.user.id),
                str(interaction.guild_id),
                reward_type.upper(),
                points
            )

            if not reward:
                await interaction.followup.send(
                    "報酬の請求処理中にエラーが発生しました。",
                    ephemeral=True
                )
                return

            # 結果の表示
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            point_unit = settings.global_settings.point_unit if settings else "ポイント"

            embed = discord.Embed(
                title="報酬交換成功",
                description=f"{points}{point_unit}を{reward_type}に交換しました。",
                color=discord.Color.green()
            )

            if reward_type == "coupon":
                embed.add_field(
                    name="クーポンコード",
                    value=f"```{reward.claim_code}```\n"
                          f"このコードは専用サイトで利用できます。",
                    inline=False
                )
            elif reward_type == "nft":
                embed.add_field(
                    name="NFTトランザクション",
                    value=f"トランザクションハッシュ:\n```{reward.claim_code}```",
                    inline=False
                )
            else:  # token
                embed.add_field(
                    name="トークン転送",
                    value=f"トランザクションハッシュ:\n```{reward.claim_code}```",
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError as e:
            await interaction.followup.send(str(e), ephemeral=True)
        except Exception as e:
            print(f"Error in claim command: {e}")
            print(traceback.format_exc())
            await interaction.followup.send(
                "予期せぬエラーが発生しました。",
                ephemeral=True
            )

    @app_commands.command(
        name="rewards_history",
        description="報酬交換履歴を表示します"
    )
    @app_commands.describe(
        status="表示したい履歴のステータス"
    )
    async def rewards_history(
        self,
        interaction: discord.Interaction,
        status: Optional[Literal["pending", "completed", "failed"]] = None
    ):
        """報酬履歴表示コマンド"""
        try:
            await interaction.response.defer(ephemeral=True)

            # 履歴の取得
            rewards = await self.bot.reward_manager.get_user_rewards(
                str(interaction.user.id),
                str(interaction.guild_id),
                status.upper() if status else None
            )

            if not rewards:
                await interaction.followup.send(
                    "報酬交換履歴がありません。",
                    ephemeral=True
                )
                return

            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            point_unit = settings.global_settings.point_unit if settings else "ポイント"

            # 履歴の表示用Embed作成
            embed = discord.Embed(
                title="報酬交換履歴",
                description="最新の交換履歴を表示します",
                color=discord.Color.blue()
            )

            for reward in rewards[:10]:  # 最新10件を表示
                status_emoji = {
                    "PENDING": "⏳",
                    "COMPLETED": "✅",
                    "FAILED": "❌"
                }.get(reward.status, "❓")

                reward_type_name = {
                    "COUPON": "クーポン",
                    "NFT": "NFT",
                    "TOKEN": "トークン"
                }.get(reward.reward_type, reward.reward_type)

                embed.add_field(
                    name=f"{status_emoji} {reward_type_name}",
                    value=f"消費ポイント: {reward.points_spent}{point_unit}\n"
                          f"交換日時: {reward.created_at.strftime('%Y/%m/%d %H:%M:%S')}\n"
                          f"ステータス: {reward.status}",
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"Error in rewards_history command: {e}")
            print(traceback.format_exc())
            await interaction.followup.send(
                "履歴の取得中にエラーが発生しました。",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Rewards(bot))