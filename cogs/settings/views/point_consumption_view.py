# cogs/settings/views/point_consumption_view.py
import discord
from .base import BaseSettingsView

class PointConsumptionSettingsView(BaseSettingsView):
    def __init__(self, settings):
        super().__init__(settings)
        self._add_buttons()

    def _add_buttons(self):
        """ボタンの追加"""
        self.add_item(discord.ui.Button(
            label="基本設定",
            style=discord.ButtonStyle.primary,
            custom_id="consumption_basic"
        ))
        self.add_item(discord.ui.Button(
            label="通知設定",
            style=discord.ButtonStyle.primary,
            custom_id="consumption_notifications"
        ))
        self.add_item(discord.ui.Button(
            label="ログ設定",
            style=discord.ButtonStyle.primary,
            custom_id="consumption_logging"
        ))
        self.add_item(discord.ui.Button(
            label="有効/無効",
            style=discord.ButtonStyle.secondary,
            custom_id="consumption_toggle"
        ))

    async def create_settings_embed(self) -> discord.Embed:
        """ポイント消費設定の表示用Embedを作成"""
        embed = self.create_base_embed(
            title="💰 ポイント消費設定",
            description="以下のボタンから設定を変更できます。"
        )
        
        # 基本情報
        embed.add_field(
            name="状態",
            value="✅ 有効" if self.settings.enabled else "❌ 無効",
            inline=True
        )
        
        # 基本設定
        embed.add_field(
            name="基本設定",
            value=f"ボタン名: {self.settings.button_name}\n"
                  f"必要ポイント: {self.settings.required_points}\n"
                  f"スレッド使用: {'はい' if self.settings.use_thread else 'いいえ'}",
            inline=False
        )
        
        # 通知設定
        notification_channel = "未設定"
        if self.settings.notification_channel_id:
            notification_channel = f"<#{self.settings.notification_channel_id}>"
            
        embed.add_field(
            name="通知設定",
            value=f"通知チャンネル: {notification_channel}\n"
                  f"完了メッセージ: {'有効' if self.settings.completion_message_enabled else '無効'}",
            inline=False
        )
        
        # ログ設定
        log_channel = "未設定"
        if self.settings.logging_channel_id:
            log_channel = f"<#{self.settings.logging_channel_id}>"
            
        embed.add_field(
            name="ログ設定",
            value=f"ログ機能: {'有効' if self.settings.logging_enabled else '無効'}\n"
                  f"ログチャンネル: {log_channel}",
            inline=False
        )
        
        return embed

    @discord.ui.button(label="設定を更新", style=discord.ButtonStyle.success)
    async def update_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        """設定の更新"""
        try:
            embed = await self.create_settings_embed()
            await self._update_message(interaction, embed=embed)
        except Exception as e:
            await self._handle_error(interaction, e)