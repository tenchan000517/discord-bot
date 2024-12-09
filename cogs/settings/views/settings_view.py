import discord
from .base import BaseSettingsView
from ..modals import GlobalSettingsModal

class SettingsView(BaseSettingsView):
    """サーバー全体の設定を管理するビュー"""
    def __init__(self, bot, settings):
        super().__init__(settings=settings)
        self.bot = bot
        self._setup_view()

    def _setup_view(self):
        """ビューの初期設定"""
        # グローバル設定
        self.add_item(GlobalSettingsButton())

        # 機能別設定ボタン
        features = {
            "gacha": "ガチャ",
            "battle": "バトル",
            "fortune": "占い"
        }
        
        for feature_id, display_name in features.items():
            enabled = self.settings.global_settings.features_enabled.get(feature_id, True)
            self.add_item(FeatureButton(feature_id, display_name, enabled))

    async def _handle_global_settings(self, interaction: discord.Interaction):
        """グローバル設定の処理"""
        try:
            # タイムゾーンと言語設定用のモーダルを表示
            await interaction.response.send_modal(GlobalSettingsModal(self.settings))
        except Exception as e:
            await self._handle_error(interaction, e)

    async def _handle_feature_settings(self, interaction: discord.Interaction, feature_id: str):
        """機能別設定の処理"""
        print(f"[INFO] _handle_feature_settings called for feature: {feature_id}, user: {interaction.user.id}")
        try:
            feature_settings = getattr(self.settings, f"{feature_id}_settings", None)
            if not feature_settings:
                print(f"[ERROR] Feature settings not found for feature: {feature_id}")
                await interaction.response.send_message(f"{feature_id}の設定が見つかりません。", ephemeral=True)
                return

            print(f"[INFO] Feature settings retrieved successfully for feature: {feature_id}")

            # ガチャ設定の場合は専用ビューを使用
            if feature_id == "gacha":
                from .gacha_view import GachaSettingsView
                view = GachaSettingsView(self.bot, feature_settings)
            else:
                view = FeatureSettingsView(self.bot, self.settings, feature_id)

            embed = await view.create_settings_embed()
            print(f"[INFO] Created embed and view for feature: {feature_id}")

            await interaction.response.edit_message(embed=embed, view=view)
            print(f"[SUCCESS] Interaction response updated for feature: {feature_id}")

        except Exception as e:
            print(f"[ERROR] Exception in _handle_feature_settings: {e}")
            await interaction.response.send_message("設定画面の表示中にエラーが発生しました。", ephemeral=True)


class FeatureSettingsView(BaseSettingsView):
    """機能別の設定を管理するビュー"""
    def __init__(self, bot, settings, feature_id):
        super().__init__(settings=settings)
        self.bot = bot
        self.feature_id = feature_id
        self._setup_view()

    def _setup_view(self):
        """ビューの初期設定"""
        # 機能の有効/無効切り替え
        enabled = self.settings.global_settings.features_enabled.get(self.feature_id, True)
        self.add_item(ToggleButton(enabled))

        # 詳細設定
        self.add_item(ConfigureButton())

        # 戻るボタン
        self.add_item(BackButton())

    async def create_feature_embed(self) -> discord.Embed:
        """機能の設定状態を表示するEmbed"""
        feature_name = {
            "gacha": "ガチャ",
            "battle": "バトル",
            "fortune": "占い"
        }.get(self.feature_id, self.feature_id.capitalize())

        embed = self.create_base_embed(
            title=f"⚙️ {feature_name}設定",
            description="以下のボタンから設定を変更できます。"
        )

        # 現在の設定状態を表示
        feature_settings = getattr(self.settings, f"{self.feature_id}_settings")
        enabled = self.settings.global_settings.features_enabled.get(self.feature_id, True)

        embed.add_field(
            name="状態",
            value="✅ 有効" if enabled else "❌ 無効",
            inline=False
        )

        # 機能固有の設定情報を追加
        if self.feature_id == "gacha":
            self._add_gacha_fields(embed, feature_settings)
        elif self.feature_id == "battle":
            self._add_battle_fields(embed, feature_settings)
        elif self.feature_id == "fortune":
            self._add_fortune_fields(embed, feature_settings)

        return embed

    def _add_gacha_fields(self, embed: discord.Embed, settings):
        """ガチャ設定の情報を追加"""
        embed.add_field(
            name="アイテム数",
            value=f"{len(settings.items)}個",
            inline=True
        )
        if settings.messages:
            embed.add_field(
                name="カスタムメッセージ",
                value="設定済み",
                inline=True
            )

    def _add_battle_fields(self, embed: discord.Embed, settings):
        """バトル設定の情報を追加"""
        embed.add_field(
            name="ポイント設定",
            value=f"キル: {settings.points_per_kill}\n優勝: {settings.winner_points}",
            inline=True
        )
        embed.add_field(
            name="開始待機時間",
            value=f"{settings.start_delay_minutes}分",
            inline=True
        )

    def _add_fortune_fields(self, embed: discord.Embed, settings):
        """占い設定の情報を追加"""
        custom_messages = getattr(settings, 'custom_messages', {})
        embed.add_field(
            name="カスタムメッセージ",
            value=f"{len(custom_messages)}件" if custom_messages else "未設定",
            inline=True
        )

# UIコンポーネント
class GlobalSettingsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="グローバル設定",
            style=discord.ButtonStyle.primary,
            custom_id="global_settings"
        )

    async def callback(self, interaction: discord.Interaction):
        await self.view._handle_global_settings(interaction)

class FeatureButton(discord.ui.Button):
    def __init__(self, feature_id: str, display_name: str, enabled: bool):
        super().__init__(
            label=f"{display_name}設定",
            style=discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary,
            custom_id=f"feature_{feature_id}"
        )
        self.feature_id = feature_id

    async def callback(self, interaction: discord.Interaction):
        print(f"[INFO] FeatureButton clicked: {self.feature_id}, by user: {interaction.user.id}")
        try:
            await self.view._handle_feature_settings(interaction, self.feature_id)
        except Exception as e:
            print(f"[ERROR] Exception in FeatureButton callback: {e}")
            await interaction.response.send_message("エラーが発生しました。", ephemeral=True)


class ToggleButton(discord.ui.Button):
    def __init__(self, enabled: bool):
        super().__init__(
            label="有効化" if not enabled else "無効化",
            style=discord.ButtonStyle.success if enabled else discord.ButtonStyle.danger,
            custom_id="toggle_feature"
        )

    async def callback(self, interaction: discord.Interaction):
        """機能の有効/無効を切り替え"""
        try:
            feature_id = self.view.feature_id
            print(f"[DEBUG] Toggle callback started - feature_id: {feature_id}")
                
            # 状態を反転
            current_state = self.view.settings.global_settings.features_enabled.get(feature_id, True)
            new_state = not current_state
            print(f"[DEBUG] Current state: {current_state}, New state: {new_state}")
                
            # 現在の機能の設定を取得
            feature_settings = getattr(self.view.settings, f"{feature_id}_settings")
            if not feature_settings:
                print("[DEBUG] Feature settings not found")
                await interaction.response.send_message(
                    "設定の更新に失敗しました。",
                    ephemeral=True
                )
                return

            # 設定を更新
            settings_manager = self.view.bot.settings_manager
            print(f"[DEBUG] Settings manager: {settings_manager}")
            
            current_settings_dict = {
                'enabled': new_state,
                'messages': feature_settings.messages.to_dict() if feature_settings.messages else None,
                'media': feature_settings.media.to_dict() if feature_settings.media else None,
                'items': feature_settings.items if hasattr(feature_settings, 'items') else None
            }
            print(f"[DEBUG] Update settings dict: {current_settings_dict}")
                
            success = await settings_manager.update_feature_settings(
                str(interaction.guild_id),
                feature_id,
                current_settings_dict
            )
            print(f"[DEBUG] Update result: {success}")
                
            if success:
                # 状態を更新
                self.view.settings.global_settings.features_enabled[feature_id] = new_state
                    
                # ボタンの表示を更新
                self.label = "有効化" if not new_state else "無効化"
                self.style = discord.ButtonStyle.success if new_state else discord.ButtonStyle.danger
                    
                # Embedを更新
                embed = await self.view.create_feature_embed()
                await interaction.response.edit_message(embed=embed, view=self.view)
            else:
                await interaction.response.send_message(
                    "設定の更新に失敗しました。",
                    ephemeral=True
                )
        except Exception as e:
            print(f"[ERROR] Failed to toggle feature: {e}")
            print(f"[ERROR] Error type: {type(e)}")
            print(f"[ERROR] Error trace:", exc_info=True)
            await interaction.response.send_message(
                "機能の切り替え中にエラーが発生しました。",
                ephemeral=True
            )

class ConfigureButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="詳細設定",
            style=discord.ButtonStyle.primary,
            custom_id="configure_feature"
        )

    async def callback(self, interaction: discord.Interaction):
        print(f"[INFO] ConfigureButton clicked by user: {interaction.user.id}")
        try:
            # Adminコグの取得
            admin_cog = self.view.bot.get_cog("Admin")
            if admin_cog:
                print(f"[INFO] Found Admin cog. Calling _show_feature_config.")
                settings = self.view.settings
                feature_id = self.view.feature_id
                await admin_cog._show_feature_config(interaction, settings, feature_id)
            else:
                print(f"[ERROR] Admin cog not found.")
                await interaction.response.send_message("管理機能が見つかりません。", ephemeral=True)
        except Exception as e:
            print(f"[ERROR] Exception in ConfigureButton callback: {e}")
            await interaction.response.send_message("エラーが発生しました。", ephemeral=True)


class BackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="戻る",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_main"
        )

    async def callback(self, interaction: discord.Interaction):
        """メイン設定画面に戻る"""
        try:
            # メインの設定ビューを再作成
            view = SettingsView(self.view.bot, self.view.settings)
            embed = self.view.create_base_embed(
                title="🛠️ サーバー設定",
                description="以下のボタンから設定を変更できます。"
            )
            
            # グローバル設定
            embed.add_field(
                name="グローバル設定",
                value=f"ポイント単位: {self.view.settings.global_settings.point_unit}\n"
                      f"タイムゾーン: {self.view.settings.global_settings.timezone}\n"
                      f"言語: {self.view.settings.global_settings.language}",
                inline=False
            )

            # 機能の有効/無効状態
            enabled_features = []
            for feature, enabled in self.view.settings.global_settings.features_enabled.items():
                status = "✅" if enabled else "❌"
                enabled_features.append(f"{feature}: {status}")
            
            embed.add_field(
                name="機能の状態",
                value="\n".join(enabled_features),
                inline=False
            )

            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            print(f"[ERROR] Failed to go back to main settings: {e}")
            await interaction.response.send_message(
                "設定画面の表示中にエラーが発生しました。",
                ephemeral=True
            )