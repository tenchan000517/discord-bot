# cogs/modals.py
import discord
import json
from typing import Optional, Dict, Any
from models.server_settings import MessageSettings, MediaSettings

class BaseSettingsModal(discord.ui.Modal):
    """設定モーダルの基本クラス"""
    def __init__(self, title: str, settings: Any):
        super().__init__(title=title)
        self.settings = settings

    async def _handle_submit_result(self, interaction: discord.Interaction, success: bool):
        """設定更新の結果に応じたメッセージを送信"""
        if success:
            await interaction.response.send_message(
                f"{self.title}を更新しました。",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "設定の更新に失敗しました。",
                ephemeral=True
            )

class GachaSettingsModal(BaseSettingsModal):
    def __init__(self, settings):
        super().__init__(title="ガチャ設定", settings=settings)

        # セットアップメッセージ設定
        self.setup_message = discord.ui.TextInput(
            label="セットアップメッセージ",
            style=discord.TextStyle.paragraph,
            placeholder="ガチャ初期設定時のメッセージ",
            required=False,
            default=getattr(settings.messages, 'setup', '') if settings.messages else '',
            max_length=1000
        )
        self.add_item(self.setup_message)

        # デイリーメッセージ設定
        self.daily_message = discord.ui.TextInput(
            label="デイリーメッセージ",
            style=discord.TextStyle.paragraph,
            placeholder="ガチャ実行時のメッセージ",
            required=False,
            default=getattr(settings.messages, 'daily', '') if settings.messages else '',
            max_length=1000
        )
        self.add_item(self.daily_message)

        # 当選メッセージ設定
        self.win_message = discord.ui.TextInput(
            label="当選メッセージ",
            style=discord.TextStyle.paragraph,
            placeholder="ガチャ当選時のメッセージ",
            required=False,
            default=getattr(settings.messages, 'win', '') if settings.messages else '',
            max_length=1000
        )
        self.add_item(self.win_message)

        # バナー画像URL
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
            if self.banner_url.value and not self.banner_url.value.startswith(('http://', 'https://')):
                await interaction.response.send_message(
                    "画像URLは http:// または https:// で始まる必要があります。",
                    ephemeral=True
                )
                return

            # 設定を更新
            updated_settings = {
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

            success = interaction.client.settings_manager.update_feature_settings(
                str(interaction.guild_id),
                'gacha',
                updated_settings
            )

            await self._handle_submit_result(interaction, success)

        except Exception as e:
            await interaction.response.send_message(
                f"エラーが発生しました: {str(e)}",
                ephemeral=True
            )

class BattleSettingsModal(BaseSettingsModal):
    def __init__(self, settings):
        super().__init__(title="バトル設定", settings=settings)

        # キル報酬ポイント
        self.points_per_kill = discord.ui.TextInput(
            label="キル報酬ポイント",
            placeholder="1キルあたりのポイント (例: 100)",
            default=str(settings.points_per_kill),
            required=True,
            min_length=1,
            max_length=5
        )
        self.add_item(self.points_per_kill)

        # 優勝報酬ポイント
        self.winner_points = discord.ui.TextInput(
            label="優勝報酬ポイント",
            placeholder="優勝賞金 (例: 1000)",
            default=str(settings.winner_points),
            required=True,
            min_length=1,
            max_length=5
        )
        self.add_item(self.winner_points)

        # 開始待機時間
        self.start_delay = discord.ui.TextInput(
            label="開始待機時間（分）",
            placeholder="バトル開始までの待機時間 (1-10)",
            default=str(settings.start_delay_minutes),
            required=True,
            min_length=1,
            max_length=2
        )
        self.add_item(self.start_delay)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # 数値のバリデーション
            points_per_kill = int(self.points_per_kill.value)
            winner_points = int(self.winner_points.value)
            start_delay = int(self.start_delay.value)

            if points_per_kill < 0 or winner_points < 0:
                await interaction.response.send_message(
                    "ポイントは0以上の値を指定してください。",
                    ephemeral=True
                )
                return

            if start_delay < 1 or start_delay > 10:
                await interaction.response.send_message(
                    "開始待機時間は1-10分の間で指定してください。",
                    ephemeral=True
                )
                return

            # 設定を更新
            updated_settings = {
                'enabled': self.settings.enabled,
                'points_per_kill': points_per_kill,
                'winner_points': winner_points,
                'start_delay_minutes': start_delay,
                'points_enabled': self.settings.points_enabled,
                'required_role_id': self.settings.required_role_id,
                'winner_role_id': self.settings.winner_role_id
            }

            success = interaction.client.settings_manager.update_feature_settings(
                str(interaction.guild_id),
                'battle',
                updated_settings
            )

            await self._handle_submit_result(interaction, success)

        except ValueError:
            await interaction.response.send_message(
                "数値の入力が正しくありません。",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"エラーが発生しました: {str(e)}",
                ephemeral=True
            )

class FortuneSettingsModal(BaseSettingsModal):
    def __init__(self, settings):
        super().__init__(title="占い設定", settings=settings)

        # カスタムメッセージ（JSON形式）
        self.custom_messages = discord.ui.TextInput(
            label="カスタムメッセージ設定",
            style=discord.TextStyle.paragraph,
            placeholder='{\n  "大吉": "とても良い1日になりそう！",\n  "吉": "良い1日になりそう！"\n}',
            required=False,
            default=json.dumps(settings.custom_messages, ensure_ascii=False, indent=2) if settings.custom_messages else '',
            max_length=1000
        )
        self.add_item(self.custom_messages)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # JSONのバリデーション
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
                'custom_messages': custom_messages
            }

            success = interaction.client.settings_manager.update_feature_settings(
                str(interaction.guild_id),
                'fortune',
                updated_settings
            )

            await self._handle_submit_result(interaction, success)

        except Exception as e:
            await interaction.response.send_message(
                f"エラーが発生しました: {str(e)}",
                ephemeral=True
            )

class PointConsumptionSettingsModal(BaseSettingsModal):
    def __init__(self, settings):
        super().__init__(title="ポイント消費設定", settings=settings)

        # ボタン表示名
        self.button_name = discord.ui.TextInput(
            label="ボタン表示名",
            placeholder="消費ボタンに表示する名前",
            required=True,
            default=settings.button_name,
            max_length=80
        )
        self.add_item(self.button_name)

        # 必要ポイント数
        self.required_points = discord.ui.TextInput(
            label="必要ポイント数",
            placeholder="消費に必要なポイント数",
            required=True,
            default=str(settings.required_points),
            max_length=10
        )
        self.add_item(self.required_points)

        # スレッド使用設定
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
            # 入力値のバリデーション
            required_points = int(self.required_points.value)
            if required_points < 0:
                await interaction.response.send_message(
                    "必要ポイント数は0以上の値を指定してください。",
                    ephemeral=True
                )
                return

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

            success = await interaction.client.settings_manager.update_feature_settings(
                str(interaction.guild_id),
                'point_consumption',
                updated_settings
            )

            await self._handle_submit_result(interaction, success)

        except ValueError:
            await interaction.response.send_message(
                "数値の入力が正しくありません。",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"エラーが発生しました: {str(e)}",
                ephemeral=True
            )