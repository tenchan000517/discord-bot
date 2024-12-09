# cogs/modals/gacha.py
import discord
from .base import BaseSettingsModal
from models.server_settings import MessageSettings, MediaSettings

class GachaSettingsModal(BaseSettingsModal):
    def __init__(self, settings):
        super().__init__(title="ガチャ設定", settings=settings)
        self._setup_fields(settings)

    def _setup_fields(self, settings):
        """フィールドのセットアップ"""
        self.setup_message = discord.ui.TextInput(
            label="セットアップメッセージ",
            style=discord.TextStyle.paragraph,
            placeholder="ガチャ初期設定時のメッセージ",
            required=False,
            default=getattr(settings.messages, 'setup', '') if settings.messages else '',
            max_length=1000
        )
        self.add_item(self.setup_message)

        self.daily_message = discord.ui.TextInput(
            label="デイリーメッセージ",
            style=discord.TextStyle.paragraph,
            placeholder="ガチャ実行時のメッセージ",
            required=False,
            default=getattr(settings.messages, 'daily', '') if settings.messages else '',
            max_length=1000
        )
        self.add_item(self.daily_message)

        self.win_message = discord.ui.TextInput(
            label="当選メッセージ",
            style=discord.TextStyle.paragraph,
            placeholder="ガチャ当選時のメッセージ",
            required=False,
            default=getattr(settings.messages, 'win', '') if settings.messages else '',
            max_length=1000
        )
        self.add_item(self.win_message)

        self.banner_url = discord.ui.TextInput(
            label="バナー画像URL",
            placeholder="https://example.com/image.png",
            required=False,
            default=settings.media.banner_gif if settings.media else '',
            max_length=200
        )
        self.add_item(self.banner_url)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # URLのバリデーション
            if self.banner_url.value:
                is_valid, error_msg = await self._validate_url(self.banner_url.value)
                if not is_valid:
                    await interaction.response.send_message(error_msg, ephemeral=True)
                    return

            # 設定を更新
            updated_settings = await self._create_updated_settings()
            success = await self._update_feature_settings(interaction, 'gacha', updated_settings)
            await self._handle_submit_result(interaction, success)

        except Exception as e:
            await interaction.response.send_message(
                f"エラーが発生しました: {str(e)}",
                ephemeral=True
            )

    async def _create_updated_settings(self) -> dict:
        """更新された設定の作成"""
        return {
            'enabled': self.settings.enabled,
            'messages': MessageSettings(
                setup=self.setup_message.value,
                daily=self.daily_message.value,
                win=self.win_message.value,
                custom_messages={}
            ).__dict__,
            'media': MediaSettings(
                banner_gif=self.banner_url.value
            ).__dict__,
            'items': self.settings.items
        }