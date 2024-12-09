# cogs/admin.py
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal
import traceback

from .settings.modals import GachaSettingsModal, BattleSettingsModal, FortuneSettingsModal
from .settings.views import SettingsView, FeatureSettingsView

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="settings", description="サーバー設定を表示または変更します")
    @app_commands.checks.has_permissions(administrator=True)
    async def settings(self, interaction: discord.Interaction):
        """サーバー設定を管理するコマンド"""
        try:
            print(f"[INFO] settings command triggered by user: {interaction.user.id}, guild: {interaction.guild_id}")
            
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            if not settings:
                print(f"[ERROR] No settings found for guild_id: {interaction.guild_id}")
                await interaction.response.send_message("設定の取得に失敗しました。", ephemeral=True)
                return

            print(f"[DEBUG] Retrieved settings type: {type(settings)}, content: {settings}")

            embed = self._create_settings_embed(settings)
            view = SettingsView(self.bot, settings)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            print(f"[ERROR] Exception in settings command: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                "設定の取得中にエラーが発生しました。",
                ephemeral=True
            )

    def _create_settings_embed(self, settings) -> discord.Embed:
        """設定表示用のEmbedを作成"""
        embed = discord.Embed(
            title="🛠️ サーバー設定",
            color=discord.Color.blue()
        )

        # グローバル設定
        embed.add_field(
            name="グローバル設定",
            value=f"ポイント単位: {settings.global_settings.point_unit}\n"
                  f"タイムゾーン: {settings.global_settings.timezone}\n"
                  f"言語: {settings.global_settings.language}",
            inline=False
        )

        # 機能の有効/無効状態
        enabled_features = []
        for feature, enabled in settings.global_settings.features_enabled.items():
            status = "✅" if enabled else "❌"
            enabled_features.append(f"{feature}: {status}")
        
        embed.add_field(
            name="機能の状態",
            value="\n".join(enabled_features),
            inline=False
        )

        return embed

    @app_commands.command(
        name="feature",
        description="特定の機能の設定を管理します"
    )
    @app_commands.describe(
        feature="設定を変更する機能を選択",
        action="実行するアクション"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def feature_settings(
        self,
        interaction: discord.Interaction,
        feature: Literal["gacha", "battle", "fortune"],
        action: Literal["view", "enable", "disable", "configure"]
    ):
        """機能ごとの詳細設定を管理"""
        try:
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            if not settings:
                await interaction.response.send_message(
                    "設定の取得に失敗しました。",
                    ephemeral=True
                )
                return

            if action == "view":
                await self._show_feature_settings(interaction, settings, feature)
            elif action in ["enable", "disable"]:
                await self._toggle_feature(interaction, settings, feature, action == "enable")
            elif action == "configure":
                await self._show_feature_config(interaction, settings, feature)

        except Exception as e:
            print(f"Error in feature_settings command: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                "設定の操作中にエラーが発生しました。",
                ephemeral=True
            )

    async def _show_feature_settings(
        self,
        interaction: discord.Interaction,
        settings,
        feature: str
    ):
        """機能の現在の設定を表示"""
        try:
            feature_settings = getattr(settings, f"{feature}_settings")
            
            # 機能別のViewを選択
            if feature == "gacha":
                from .settings.views.gacha_view import GachaSettingsView
                view = GachaSettingsView(self.bot, feature_settings)
            else:
                view = FeatureSettingsView(self.bot, settings, feature)
            
            # Embedを作成
            embed = await view.create_settings_embed()
            
            # 表示
            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )
        except Exception as e:
            print(f"Error showing feature settings: {e}")
            await interaction.response.send_message(
                "設定の表示中にエラーが発生しました。",
                ephemeral=True
            )

    def _create_feature_embed(self, feature: str, settings, embed: discord.Embed) -> discord.Embed:
        """機能ごとの設定Embedを作成"""
        if feature == "gacha":
            embed.add_field(
                name="基本設定",
                value=f"有効状態: {'有効' if settings.enabled else '無効'}\n"
                      f"アイテム数: {len(settings.items)}",
                inline=False
            )
            if settings.messages:
                embed.add_field(
                    name="メッセージ設定",
                    value="カスタマイズ済み",
                    inline=False
                )
        elif feature == "battle":
            embed.add_field(
                name="基本設定",
                value=f"有効状態: {'有効' if settings.enabled else '無効'}\n"
                      f"キルポイント: {settings.points_per_kill}\n"
                      f"優勝ポイント: {settings.winner_points}",
                inline=False
            )
        elif feature == "fortune":
            embed.add_field(
                name="基本設定",
                value=f"有効状態: {'有効' if settings.enabled else '無効'}",
                inline=False
            )
        return embed

    async def _toggle_feature(
        self,
        interaction: discord.Interaction,
        settings,
        feature: str,
        enable: bool
    ):
        """機能の有効/無効を切り替え"""
        settings.global_settings.features_enabled[feature] = enable
        success = self.bot.settings_manager.update_settings(
            str(interaction.guild_id),
            settings
        )

        if success:
            await interaction.response.send_message(
                f"{feature.capitalize()}機能を{'有効' if enable else '無効'}にしました。",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "設定の更新に失敗しました。",
                ephemeral=True
            )

    async def _show_feature_config(
        self,
        interaction: discord.Interaction,
        settings,
        feature: str
    ):
        """機能の詳細設定画面を表示"""
        try:
            modal_class = {
                'gacha': GachaSettingsModal,
                'battle': BattleSettingsModal,
                'fortune': FortuneSettingsModal
            }.get(feature)

            if modal_class:
                feature_settings = getattr(settings, f"{feature}_settings")
                modal = modal_class(feature_settings, self.bot.settings_manager)
                await interaction.response.send_modal(modal)
            else:
                await interaction.response.send_message(
                    "無効な機能が指定されました。",
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error showing feature config: {e}")
            await interaction.response.send_message(
                "設定画面の表示中にエラーが発生しました。",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Admin(bot))