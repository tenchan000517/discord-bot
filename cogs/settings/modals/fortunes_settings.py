import discord
from typing import Dict
import json
from .base import BaseSettingsModal

class FortuneSettingsModal(BaseSettingsModal):
    def __init__(self, settings):
        super().__init__(title="占い設定", settings=settings)
        self._setup_fields(settings)

    def _setup_fields(self, settings):
        """フィールドのセットアップ"""
        # カスタムメッセージ設定
        self.custom_messages = discord.ui.TextInput(
            label="カスタムメッセージ設定",
            style=discord.TextStyle.paragraph,
            placeholder='{\n  "大吉": "とても良い1日になりそう！",\n  "吉": "良い1日になりそう！"\n}',
            required=False,
            default=json.dumps(settings.custom_messages, ensure_ascii=False, indent=2) if hasattr(settings, 'custom_messages') and settings.custom_messages else '',
            max_length=1000
        )
        self.add_item(self.custom_messages)

        # 日替わりメッセージ
        self.daily_message = discord.ui.TextInput(
            label="日替わりメッセージ",
            style=discord.TextStyle.paragraph,
            placeholder="今日はすでに占いをしています。明日また挑戦してください！",
            required=False,
            default=getattr(settings, 'daily_message', ''),
            max_length=200
        )
        self.add_item(self.daily_message)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # カスタムメッセージのJSONバリデーション
            custom_messages = {}
            if self.custom_messages.value:
                try:
                    custom_messages = json.loads(self.custom_messages.value)
                    if not isinstance(custom_messages, dict):
                        raise ValueError("JSONはオブジェクト形式である必要があります")
                except json.JSONDecodeError:
                    await interaction.response.send_message(
                        "カスタムメッセージの形式が正しくありません。有効なJSONを入力してください。",
                        ephemeral=True
                    )
                    return

            # 設定を更新
            updated_settings = {
                'enabled': self.settings.enabled,
                'custom_messages': custom_messages,
                'daily_message': self.daily_message.value
            }

            success = await self._update_feature_settings(
                interaction,
                'fortune',
                updated_settings
            )
            await self._handle_submit_result(interaction, success)

        except Exception as e:
            await interaction.response.send_message(
                f"エラーが発生しました: {str(e)}",
                ephemeral=True
            )