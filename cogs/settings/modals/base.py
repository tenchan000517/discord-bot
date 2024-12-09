# cogs/settings/modals/base.py
import discord
from typing import Any, Tuple, Optional

class BaseSettingsModal(discord.ui.Modal):
    """設定モーダルの基本クラス"""
    def __init__(self, title: str, settings: Any):
        super().__init__(title=title)
        self.settings = settings

    async def _handle_submit_result(self, interaction: discord.Interaction, success: bool, message: str = None):
        """設定更新の結果に応じたメッセージを送信"""
        if success:
            await interaction.response.send_message(
                message or f"{self.title}を更新しました。",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                message or "設定の更新に失敗しました。",
                ephemeral=True
            )

    async def _validate_number(
        self, 
        value: str, 
        min_val: Optional[int] = None, 
        max_val: Optional[int] = None
    ) -> Tuple[bool, Optional[int], str]:
        """
        数値のバリデーション
        Returns:
            Tuple[valid: bool, value: Optional[int], error_message: str]
        """
        try:
            num = int(value)
            if min_val is not None and num < min_val:
                return False, None, f"値は{min_val}以上である必要があります"
            if max_val is not None and num > max_val:
                return False, None, f"値は{max_val}以下である必要があります"
            return True, num, ""
        except ValueError:
            return False, None, "有効な数値を入力してください"

    async def _validate_url(self, url: str) -> Tuple[bool, str]:
        """
        URLのバリデーション
        Returns:
            Tuple[valid: bool, error_message: str]
        """
        if not url:
            return True, ""
        if not url.startswith(('http://', 'https://')):
            return False, "URLはhttp://またはhttps://で始まる必要があります"
        return True, ""

    async def _update_feature_settings(
        self,
        interaction: discord.Interaction,
        feature: str,
        settings: dict
    ) -> bool:
        """機能設定の更新"""
        try:
            return interaction.client.settings_manager.update_feature_settings(
                str(interaction.guild_id),
                feature,
                settings
            )
        except Exception as e:
            print(f"Error updating {feature} settings: {e}")
            return False