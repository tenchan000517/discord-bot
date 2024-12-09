# cogs/settings/views/base.py
import discord
from typing import Optional, Any

class BaseSettingsView(discord.ui.View):
    """設定ビューの基本クラス"""
    def __init__(self, settings: Any, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.settings = settings
        
    async def _update_message(self, interaction: discord.Interaction, content: str = None, embed: discord.Embed = None):
        """メッセージを更新"""
        try:
            await interaction.response.edit_message(content=content, embed=embed, view=self)
        except discord.errors.InteractionResponded:
            await interaction.edit_original_response(content=content, embed=embed, view=self)

    async def _handle_error(self, interaction: discord.Interaction, error: Exception):
        """エラーハンドリング"""
        error_msg = f"エラーが発生しました: {str(error)}"
        try:
            await interaction.response.send_message(error_msg, ephemeral=True)
        except discord.errors.InteractionResponded:
            await interaction.followup.send(error_msg, ephemeral=True)
        
    def create_base_embed(self, title: str, description: str = None) -> discord.Embed:
        """基本的な設定用Embedを作成"""
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )