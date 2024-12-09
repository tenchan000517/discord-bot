# cogs/modals/battle.py
import discord
from .base import BaseSettingsModal

class BattleSettingsModal(BaseSettingsModal):
    def __init__(self, settings):
        super().__init__(title="バトル設定", settings=settings)
        self._setup_fields(settings)

    def _setup_fields(self, settings):
        """フィールドのセットアップ"""
        self.points_per_kill = discord.ui.TextInput(
            label="キル報酬ポイント",
            placeholder="1キルあたりのポイント (例: 100)",
            default=str(settings.points_per_kill),
            required=True,
            min_length=1,
            max_length=5
        )
        self.add_item(self.points_per_kill)

        self.winner_points = discord.ui.TextInput(
            label="優勝報酬ポイント",
            placeholder="優勝賞金 (例: 1000)",
            default=str(settings.winner_points),
            required=True,
            min_length=1,
            max_length=5
        )
        self.add_item(self.winner_points)

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
            valid, points_per_kill, error_msg = await self._validate_number(
                self.points_per_kill.value,
                min_val=0
            )
            if not valid:
                await interaction.response.send_message(
                    f"キル報酬ポイントの値が無効です: {error_msg}",
                    ephemeral=True
                )
                return

            valid, winner_points, error_msg = await self._validate_number(
                self.winner_points.value,
                min_val=0
            )
            if not valid:
                await interaction.response.send_message(
                    f"優勝報酬ポイントの値が無効です: {error_msg}",
                    ephemeral=True
                )
                return

            valid, start_delay, error_msg = await self._validate_number(
                self.start_delay.value,
                min_val=1,
                max_val=10
            )
            if not valid:
                await interaction.response.send_message(
                    f"開始待機時間の値が無効です: {error_msg}",
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

            success = await self._update_feature_settings(interaction, 'battle', updated_settings)
            await self._handle_submit_result(interaction, success)

        except Exception as e:
            await interaction.response.send_message(
                f"エラーが発生しました: {str(e)}",
                ephemeral=True
            )