import discord
from .base import BaseSettingsView
from ..modals.gacha_settings import GachaSettingsModal
from ..modals.gacha_items import GachaItemsView

class GachaSettingsView(BaseSettingsView):
    def __init__(self, bot, settings):
        super().__init__(settings)
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """インタラクションの権限チェック"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "この操作には管理者権限が必要です。", 
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="無効化",
        style=discord.ButtonStyle.danger,
        custom_id="toggle_gacha",
        row=0
    )
    async def toggle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ガチャ機能の有効/無効を切り替え"""
        try:
            # 状態を反転
            self.settings.enabled = not self.settings.enabled
            
            # 設定を更新
            success = await self.bot.settings_manager.update_feature_settings(
                str(interaction.guild_id),
                'gacha',
                {'enabled': self.settings.enabled}
            )

            if success:
                # ボタンの表示を更新
                button.label = "無効化" if self.settings.enabled else "有効化"
                button.style = discord.ButtonStyle.danger if self.settings.enabled else discord.ButtonStyle.success

                # Embedを更新
                embed = await self.create_settings_embed()
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await interaction.response.send_message(
                    "設定の更新に失敗しました。",
                    ephemeral=True
                )

        except Exception as e:
            await self._handle_error(interaction, e)

    @discord.ui.button(
        label="詳細設定",
        style=discord.ButtonStyle.primary,
        custom_id="configure_gacha",
        row=0
    )
    async def configure_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """詳細設定モーダルを表示"""
        try:
            modal = GachaSettingsModal(self.settings, self.bot.settings_manager)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await self._handle_error(interaction, e)

    @discord.ui.button(
        label="アイテム設定",
        style=discord.ButtonStyle.primary,
        custom_id="items_gacha",
        row=0
    )
    async def items_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """アイテム設定画面を表示"""
        try:
            view = GachaItemsView(self.settings, self.bot.settings_manager)
            await interaction.response.edit_message(
                content="🎲 ガチャアイテム設定\n登録されているアイテムの編集や新規追加ができます。",
                embed=None,  # 既存のembedをクリア
                view=view
            )
        except Exception as e:
            await self._handle_error(interaction, e)


    @discord.ui.button(
        label="戻る",
        style=discord.ButtonStyle.secondary,
        custom_id="back_gacha",
        row=1
    )
    
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """メイン設定画面に戻る"""
        from .settings_view import SettingsView
        try:
            view = SettingsView(self.bot, self.settings)
            embed = await view.create_settings_embed()
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            await self._handle_error(interaction, e)

    async def create_settings_embed(self) -> discord.Embed:
        """ガチャ設定の表示用Embedを作成"""
        embed = discord.Embed(
            title="🎲 ガチャ設定",
            description="以下のボタンから設定を変更できます。",
            color=discord.Color.blue()
        )
        
        # 基本情報
        embed.add_field(
            name="状態",
            value="✅ 有効" if self.settings.enabled else "❌ 無効",
            inline=True
        )

        # メッセージ設定の状態
        if self.settings.messages:
            message_status = "カスタマイズ済み"
        else:
            message_status = "デフォルト"
        embed.add_field(
            name="メッセージ設定",
            value=message_status,
            inline=True
        )
        
        # アイテム情報
        if self.settings.items:
            items_info = "\n".join([
                f"・{item['name']} (確率: {item['weight']}%, {item['points']}ポイント)" 
                for item in self.settings.items[:3]
            ])
            if len(self.settings.items) > 3:
                items_info += f"\n...他{len(self.settings.items) - 3}件"
        else:
            items_info = "設定されていません"

        embed.add_field(
            name="登録アイテム",
            value=items_info,
            inline=False
        )

        # バナー画像の設定状態
        if self.settings.media and self.settings.media.banner_gif:
            banner_status = "設定済み"
            embed.set_image(url=self.settings.media.banner_gif)
        else:
            banner_status = "未設定"

        embed.add_field(
            name="バナー画像",
            value=banner_status,
            inline=True
        )
        
        return embed

    async def _handle_error(self, interaction: discord.Interaction, error: Exception):
        """エラーハンドリング"""
        print(f"Error in GachaSettingsView: {error}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "エラーが発生しました。",
                    ephemeral=True
                )
        except Exception:
            pass