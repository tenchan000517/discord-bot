# cogs/points_consumption.py
import discord
from discord import app_commands
from discord.ext import commands
import traceback
from datetime import datetime
import pytz

class PointsConsumption(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.requests = {}  # ギルドIDごとのリクエストを保持

    async def setup_consumption_panel(self, channel_id: str, settings) -> None:
        """消費パネルのセットアップ"""
        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                print(f"Channel not found: {channel_id}")
                return

            # サーバー設定を取得してpoint_unitを参照
            server_settings = await self.bot.get_server_settings(str(channel.guild.id))
            point_unit = server_settings.global_settings.point_unit

            embed = discord.Embed(
                title="ポイント消費",
                description=f"クリックして{settings.required_points}{point_unit}を消費します",
                color=discord.Color.blue()
            )

            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(
                label=settings.button_name,
                style=discord.ButtonStyle.primary,
                custom_id="consume_points"
            ))

            await channel.send(embed=embed, view=view)

        except Exception as e:
            print(f"Error in setup_consumption_panel: {e}")
            print(traceback.format_exc())

    async def create_consumption_request(
        self,
        guild_id: str,
        user_id: str,
        points: int,
        thread_id: str = None
    ) -> dict:
        timestamp = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
        request = {
            'guild_id': guild_id,
            'user_id': user_id,
            'points': points,
            'timestamp': timestamp,
            'thread_id': thread_id,
            'status': 'pending'
        }

        if guild_id not in self.requests:
            self.requests[guild_id] = {}
        self.requests[guild_id][timestamp] = request

        return request

    async def process_request(self, guild_id: str, timestamp: str, status: str) -> bool:
        if guild_id in self.requests and timestamp in self.requests[guild_id]:
            self.requests[guild_id][timestamp]['status'] = status
            return True
        return False

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """ボタンのインタラクションハンドリング"""
        if not interaction.data or 'custom_id' not in interaction.data:
            return

        if interaction.data['custom_id'] == 'consume_points':
            await self.handle_consume_button(interaction)
        elif interaction.data['custom_id'].startswith('approve_consume_'):
            await self.handle_approve_button(interaction)
        elif interaction.data['custom_id'].startswith('cancel_consume_'):
            await self.handle_cancel_button(interaction)

    # ①通知チャンネルの設定　②運営のメンション　③ポイント消費リクエストメッセージのプライベート化　④スレッド作成の機能　⑤消費ポイントの設定　⑥ログ送信機能　⑥オートメーションとの絡み
    async def handle_consume_button(self, interaction: discord.Interaction):
        """消費ボタンのハンドリング"""
        try:
            # サーバー設定を取得
            settings = await self.bot.get_server_settings(str(interaction.guild_id))
            if not settings or not settings.point_consumption_settings:
                await interaction.response.send_message("ポイント消費機能が設定されていません。", ephemeral=True)
                return

            consumption_settings = settings.point_consumption_settings

            # 消費リクエストを作成
            thread_id = None
            if consumption_settings.use_thread:
                # スレッドを作成
                thread = await interaction.channel.create_thread(
                    name=f"ポイント消費-{interaction.user.name}",
                    auto_archive_duration=1440
                )
                thread_id = str(thread.id)

            # ポイントの確認
            user_points = await self.bot.point_manager.get_points(str(interaction.guild_id), str(interaction.user.id))
            if user_points < consumption_settings.required_points:
                await interaction.response.send_message(
                    "ポイントが不足しています。",
                    ephemeral=True
                )
                return

            request = await self.create_consumption_request(
                str(interaction.guild_id),
                str(interaction.user.id),
                consumption_settings.required_points,
                thread_id
            )

            if not request:
                await interaction.response.send_message(
                    "ポイントが不足しています。",
                    ephemeral=True
                )
                return

            # 承認ボタンを作成
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(
                label="承認",
                style=discord.ButtonStyle.success,
                custom_id=f"approve_consume_{request['timestamp']}"
            ))
            view.add_item(discord.ui.Button(
                label="キャンセル",
                style=discord.ButtonStyle.danger,
                custom_id=f"cancel_consume_{request['timestamp']}"
            ))

            # 通知メッセージを作成
            embed = discord.Embed(
                title="ポイント消費リクエスト",
                description=f"{interaction.user.mention}が{consumption_settings.required_points}{settings.global_settings.point_unit}の消費を申請しました。",
                color=discord.Color.blue()
            )

            # 通知を送信 改善の余地があるかも データベースとの兼ね合いを要設計 現状はひとまずカレントチャンネルをデフォルトに
            notification_channel_id = consumption_settings.notification_channel_id
            if notification_channel_id:
                notification_channel = self.bot.get_channel(int(notification_channel_id))
            else:
                notification_channel = interaction.channel  # カレントチャンネルをデフォルトにする

            if notification_channel:
                mention_text = " ".join(f"<@&{role_id}>" for role_id in consumption_settings.mention_role_ids)
                await notification_channel.send(
                    content=mention_text if mention_text else None,
                    embed=embed,
                    view=view
                )

            await interaction.response.send_message(
                "ポイント消費リクエストを送信しました。",
                ephemeral=True
            )

            # ログ記録
            if consumption_settings.logging_enabled and 'click' in consumption_settings.logging_actions:
                log_channel = self.bot.get_channel(int(consumption_settings.logging_channel_id))
                if log_channel:
                    await log_channel.send(
                        f"ユーザー {interaction.user.mention} がポイント消費ボタンをクリックしました。"
                    )

        except Exception as e:
            print(f"Error in handle_consume_button: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                "エラーが発生しました。",
                ephemeral=True
            )

    async def handle_approve_button(self, interaction: discord.Interaction):
        """承認ボタンのハンドリング"""
        try:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "管理者権限が必要です。",
                    ephemeral=True
                )
                return

            timestamp = interaction.data['custom_id'].replace('approve_consume_', '')
            guild_id = str(interaction.guild_id)
            
            # リクエストの存在確認とデータ取得
            if guild_id not in self.requests or timestamp not in self.requests[guild_id]:
                await interaction.response.send_message(
                    "リクエストが見つかりません。",
                    ephemeral=True
                )
                print(f"リクエストが見つかりません - guild_id: {guild_id}, timestamp: {timestamp}")
                return

            # リクエストデータから必要な情報を取得
            request_data = self.requests[guild_id][timestamp]
            original_user_id = request_data['user_id']  # 元のリクエストユーザーのID
            points_to_consume = request_data['points']
            print(f"消費リクエストのポイント: {points_to_consume}")

            # 承認前のポイント確認
            print(f"承認前のポイント確認:")
            current_points = await self.bot.point_manager.get_points(guild_id, original_user_id)
            print(f"現在のポイント: {current_points}")
            
            # ポイント消費実行
            success = await self.bot.point_manager.consume_points(
                guild_id,
                original_user_id,  # 元のリクエストユーザーのID
                points_to_consume,
                str(interaction.user.id)  # 承認した管理者のID
            )

            # 処理後のポイント確認
            if success:
                new_points = await self.bot.point_manager.get_points(guild_id, original_user_id)
                print(f"処理後のポイント: {new_points}")
                print(f"ポイント変動: {new_points - current_points}")

                # リクエストの状態を更新
                await self.process_request(guild_id, timestamp, 'completed')

                # 完了メッセージの送信
                settings = await self.bot.get_server_settings(str(interaction.guild_id))
                if settings.point_consumption_settings.completion_message_enabled:
                    original_user = interaction.guild.get_member(int(original_user_id))
                    if original_user:
                        await interaction.channel.send(
                            f"{original_user.mention}のポイント消費が完了しました。"
                        )

                # ログ記録
                if settings.point_consumption_settings.logging_enabled and 'complete' in settings.point_consumption_settings.logging_actions:
                    log_channel = self.bot.get_channel(int(settings.point_consumption_settings.logging_channel_id))
                    if log_channel:
                        await log_channel.send(
                            f"管理者 {interaction.user.mention} が {points_to_consume}ポイントの消費を承認しました。"
                            f"\n対象ユーザー: {original_user.mention if original_user else original_user_id}"
                        )

                await interaction.response.send_message(
                    "ポイント消費が完了しました。",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "ポイント消費に失敗しました。",
                    ephemeral=True
                )

        except Exception as e:
            print(f"Error in handle_approve_button: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                "エラーが発生しました。",
                ephemeral=True
            )

    async def handle_cancel_button(self, interaction: discord.Interaction):
        """キャンセルボタンのハンドリング"""
        try:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "管理者権限が必要です。",
                    ephemeral=True
                )
                return

            timestamp = interaction.data['custom_id'].replace('cancel_consume_', '')
            success = await self.bot.point_manager.cancel_consumption_request(
                str(interaction.guild_id),
                timestamp,
                str(interaction.user.id)
            )

            if success:
                settings = await self.bot.get_server_settings(str(interaction.guild_id))
                if settings.point_consumption_settings.completion_message_enabled:
                    await interaction.channel.send(
                        f"{interaction.user.mention}のポイント消費がキャンセルされました。"
                    )

                # ログ記録
                if settings.point_consumption_settings.logging_enabled and 'cancel' in settings.point_consumption_settings.logging_actions:
                    log_channel = self.bot.get_channel(int(settings.point_consumption_settings.logging_channel_id))
                    if log_channel:
                        await log_channel.send(
                            f"管理者 {interaction.user.mention} がポイント消費をキャンセルしました。"
                        )

            await interaction.response.send_message(
                "キャンセルが完了しました。",
                ephemeral=True
            )

        except Exception as e:
            print(f"Error in handle_cancel_button: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                "エラーが発生しました。",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(PointsConsumption(bot))

# ①管理者だけでなく設定でボタンクリック可能なロールを設定できるようにする
# ②ポイントの増減をオートメーションに伝えるだけ伝える（必要があれば※オートメーションの方で勝手にポイント増減を感知できてればわざわざ都度都度通知の必要ない）
# ③若干このcogとpoint_manager.pyの機能が被ってる気がする