# cogs/settings/modals/point_consumption_settings.py
import discord
from .base import BaseSettingsModal

class PointConsumptionSettingsModal(BaseSettingsModal):
    def __init__(self, settings):
        super().__init__(title="ポイント消費設定", settings=settings)
        self._setup_fields(settings)

    def _setup_fields(self, settings):
        """フィールドのセットアップ"""
        self.button_name = discord.ui.TextInput(
            label="ボタン表示名",
            placeholder="消費ボタンに表示する名前",
            required=True,
            default=settings.button_name,
            max_length=80
        )
        self.add_item(self.button_name)

        self.required_points = discord.ui.TextInput(
            label="必要ポイント数",
            placeholder="消費に必要なポイント数",
            required=True,
            default=str(settings.required_points),
            max_length=10
        )
        self.add_item(self.required_points)

        self.use_thread = discord.ui.TextInput(
            label="スレッドを使用",
            placeholder="true または false",
            required=True,
            default=str(settings.use_thread).lower(),
            max_length=5
        )
        self.add_item(self.use_thread)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # 数値のバリデーション
            valid, required_points, error_msg = await self._validate_number(
                self.required_points.value,
                min_val=0
            )
            if not valid:
                await interaction.response.send_message(
                    f"必要ポイント数の値が無効です: {error_msg}",
                    ephemeral=True
                )
                return

            # スレッド使用設定のバリデーション
            use_thread = self.use_thread.value.lower() == 'true'

            # 設定を更新
            updated_settings = {
                'enabled': self.settings.enabled,
                'button_name': self.button_name.value,
                'required_points': required_points,
                'use_thread': use_thread,
                'channel_id': self.settings.channel_id,
                'notification_channel_id': self.settings.notification_channel_id,
                'mention_role_ids': self.settings.mention_role_ids,
                'completion_message_enabled': self.settings.completion_message_enabled,
                'logging_enabled': self.settings.logging_enabled,
                'logging_channel_id': self.settings.logging_channel_id,
                'logging_actions': self.settings.logging_actions
            }

            success = await self._update_feature_settings(
                interaction,
                'point_consumption',
                updated_settings
            )
            await self._handle_submit_result(interaction, success)

        except Exception as e:
            await interaction.response.send_message(
                f"エラーが発生しました: {str(e)}",
                ephemeral=True
            )