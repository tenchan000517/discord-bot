import discord
from .base import BaseSettingsModal

class GlobalSettingsModal(BaseSettingsModal):
    def __init__(self, settings):
        super().__init__(title="グローバル設定", settings=settings)
        self._setup_fields(settings)

    def _setup_fields(self, settings):
        """フィールドのセットアップ"""
        self.point_unit = discord.ui.TextInput(
            label="ポイント単位",
            placeholder="例: コイン、ポイント、など",
            default=settings.global_settings.point_unit,
            required=True,
            max_length=10
        )
        self.add_item(self.point_unit)

        self.timezone = discord.ui.TextInput(
            label="タイムゾーン",
            placeholder="例: Asia/Tokyo",
            default=settings.global_settings.timezone,
            required=True,
            max_length=30
        )
        self.add_item(self.timezone)

        self.language = discord.ui.TextInput(
            label="言語",
            placeholder="例: ja",
            default=settings.global_settings.language,
            required=True,
            max_length=5
        )
        self.add_item(self.language)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # タイムゾーンの検証
            try:
                import pytz
                if self.timezone.value not in pytz.all_timezones:
                    await interaction.response.send_message(
                        "無効なタイムゾーンが指定されました。",
                        ephemeral=True
                    )
                    return
            except ImportError:
                # pytzが利用できない場合は検証をスキップ
                pass

            # 言語コードの検証
            valid_languages = ['ja']  # 現在サポートしている言語
            if self.language.value not in valid_languages:
                await interaction.response.send_message(
                    "現在サポートされていない言語が指定されました。",
                    ephemeral=True
                )
                return

            # グローバル設定を更新
            self.settings.global_settings.point_unit = self.point_unit.value
            self.settings.global_settings.timezone = self.timezone.value
            self.settings.global_settings.language = self.language.value

            # 設定を保存
            success = interaction.client.settings_manager.update_settings(
                str(interaction.guild_id),
                self.settings
            )

            await self._handle_submit_result(interaction, success)

        except Exception as e:
            await interaction.response.send_message(
                f"エラーが発生しました: {str(e)}",
                ephemeral=True
            )