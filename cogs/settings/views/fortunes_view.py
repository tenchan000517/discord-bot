# cogs/settings/views/fortunes_view.py
import discord
from .base import BaseSettingsView

class FortuneSettingsView(BaseSettingsView):
    def __init__(self, settings):
        super().__init__(settings)
        self._add_buttons()

    def _add_buttons(self):
        """ボタンの追加"""
        self.add_item(discord.ui.Button(
            label="メッセージ設定",
            style=discord.ButtonStyle.primary,
            custom_id="fortune_messages"
        ))
        self.add_item(discord.ui.Button(
            label="確率設定",
            style=discord.ButtonStyle.primary,
            custom_id="fortune_probabilities"
        ))
        self.add_item(discord.ui.Button(
            label="有効/無効",
            style=discord.ButtonStyle.secondary,
            custom_id="fortune_toggle"
        ))

    async def create_settings_embed(self) -> discord.Embed:
        """占い設定の表示用Embedを作成"""
        embed = self.create_base_embed(
            title="🔮 占い設定",
            description="以下のボタンから設定を変更できます。"
        )
        
        # 基本情報
        embed.add_field(
            name="状態",
            value="✅ 有効" if self.settings.enabled else "❌ 無効",
            inline=True
        )
        
        # カスタムメッセージ
        if hasattr(self.settings, 'custom_messages') and self.settings.custom_messages:
            messages_info = "\n".join([
                f"・{key}: {value[:30]}..." if len(value) > 30 else f"・{key}: {value}"
                for key, value in list(self.settings.custom_messages.items())[:3]
            ])
            if len(self.settings.custom_messages) > 3:
                messages_info += f"\n...他{len(self.settings.custom_messages) - 3}件"
            embed.add_field(
                name="カスタムメッセージ",
                value=messages_info,
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