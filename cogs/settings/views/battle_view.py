# cogs/settings/views/battle_view.py
import discord
from .base import BaseSettingsView

class BattleSettingsView(BaseSettingsView):
    def __init__(self, settings):
        super().__init__(settings)
        self._add_buttons()

    def _add_buttons(self):
        """ボタンの追加"""
        self.add_item(discord.ui.Button(
            label="ポイント設定",
            style=discord.ButtonStyle.primary,
            custom_id="battle_points"
        ))
        self.add_item(discord.ui.Button(
            label="ロール設定",
            style=discord.ButtonStyle.primary,
            custom_id="battle_roles"
        ))
        self.add_item(discord.ui.Button(
            label="タイミング設定",
            style=discord.ButtonStyle.primary,
            custom_id="battle_timing"
        ))
        self.add_item(discord.ui.Button(
            label="有効/無効",
            style=discord.ButtonStyle.secondary,
            custom_id="battle_toggle"
        ))

    async def create_settings_embed(self) -> discord.Embed:
        """バトル設定の表示用Embedを作成"""
        embed = self.create_base_embed(
            title="⚔️ バトル設定",
            description="以下のボタンから設定を変更できます。"
        )
        
        # 基本情報
        embed.add_field(
            name="状態",
            value="✅ 有効" if self.settings.enabled else "❌ 無効",
            inline=True
        )
        
        # ポイント設定
        embed.add_field(
            name="ポイント設定",
            value=f"キル報酬: {self.settings.points_per_kill}\n"
                  f"優勝報酬: {self.settings.winner_points}",
            inline=False
        )
        
        # 開始時間
        embed.add_field(
            name="開始待機時間",
            value=f"{self.settings.start_delay_minutes}分",
            inline=True
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