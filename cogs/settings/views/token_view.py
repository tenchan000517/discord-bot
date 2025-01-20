import discord
from .base import BaseSettingsView  # 正しい
from ..modals.token_settings import TokenSettingsModal
from utils.token_operations import TokenOperations
import logging

logger = logging.getLogger(__name__)

class TokenSettingsView(BaseSettingsView):  # BaseViewではなくBaseSettingsViewを継承
    def __init__(self, bot):
        super().__init__(timeout=180)
        self.bot = bot
        self.token_operations = TokenOperations()

    async def start(self, interaction: discord.Interaction):
        """設定ビューの表示開始"""
        embed = await self.create_settings_embed(interaction.guild_id)
        await interaction.response.send_message(
            embed=embed,
            view=self,
            ephemeral=True
        )

    async def create_settings_embed(self, guild_id: int) -> discord.Embed:
        """設定情報を表示するEmbedを作成"""
        settings = await self.token_operations.get_token_settings(str(guild_id))
        
        embed = discord.Embed(
            title="🪙 トークン設定",
            color=discord.Color.blue()
        )

        if settings and settings.get('enabled'):
            embed.add_field(
                name="ネットワーク",
                value=f"ID: {settings.get('networkId', 'N/A')}",
                inline=False
            )
            embed.add_field(
                name="コントラクト",
                value=f"```{settings.get('contractAddress', 'N/A')}```",
                inline=False
            )
            embed.add_field(
                name="トークン情報",
                value=f"シンボル: {settings.get('tokenSymbol', 'N/A')}\n"
                      f"デシマル: {settings.get('decimals', 'N/A')}",
                inline=False
            )
            embed.add_field(
                name="ステータス",
                value="✅ 有効",
                inline=False
            )
        else:
            embed.add_field(
                name="ステータス",
                value="❌ 未設定",
                inline=False
            )

        embed.set_footer(text="下のボタンから設定を変更できます")
        return embed

    @discord.ui.button(
        label="設定を変更",
        style=discord.ButtonStyle.primary,
        custom_id="token_settings:edit"
    )
    async def edit_settings(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        """設定変更モーダルを表示"""
        try:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "この操作には管理者権限が必要です。",
                    ephemeral=True
                )
                return

            modal = TokenSettingsModal()
            await interaction.response.send_modal(modal)

        except Exception as e:
            logger.error(f"Edit settings error: {str(e)}")
            await interaction.response.send_message(
                "エラーが発生しました。",
                ephemeral=True
            )

    @discord.ui.button(
        label="設定を無効化",
        style=discord.ButtonStyle.danger,
        custom_id="token_settings:disable"
    )
    async def disable_settings(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        """トークン設定を無効化"""
        try:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "この操作には管理者権限が必要です。",
                    ephemeral=True
                )
                return

            settings = await self.token_operations.get_token_settings(str(interaction.guild_id))
            if not settings or not settings.get('enabled'):
                await interaction.response.send_message(
                    "トークン設定は既に無効化されています。",
                    ephemeral=True
                )
                return

            # 設定の無効化
            settings['enabled'] = False
            success = await self.token_operations.update_token_settings(
                server_id=str(interaction.guild_id),
                **settings
            )

            if success:
                # Embedの更新
                embed = await self.create_settings_embed(interaction.guild_id)
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await interaction.response.send_message(
                    "設定の無効化に失敗しました。",
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Disable settings error: {str(e)}")
            await interaction.response.send_message(
                "エラーが発生しました。",
                ephemeral=True
            )

    @discord.ui.button(
        label="更新",
        style=discord.ButtonStyle.secondary,
        custom_id="token_settings:refresh"
    )
    async def refresh_view(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        """表示を更新"""
        try:
            embed = await self.create_settings_embed(interaction.guild_id)
            await interaction.response.edit_message(embed=embed, view=self)
        
        except Exception as e:
            logger.error(f"Refresh view error: {str(e)}")
            await interaction.response.send_message(
                "表示の更新に失敗しました。",
                ephemeral=True
            )