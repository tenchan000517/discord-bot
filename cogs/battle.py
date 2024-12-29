import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime
import traceback
from typing import Optional

from models.battle import BattleGame, BattleStatus, EventType
from utils.battle_events import generate_battle_event, format_round_message
from utils.point_manager import PointSource  # 追加

class BattleView(discord.ui.View):
    def __init__(self, game: BattleGame, cog):
        super().__init__(timeout=None)
        self.game = game
        self.cog = cog

    @discord.ui.button(label="参加", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """バトルに参加"""
        try:
            if self.game.status != BattleStatus.WAITING:
                await interaction.response.send_message("現在参加を受け付けていません。", ephemeral=True)
                return

            user_id = str(interaction.user.id)

            # ロール要件チェック
            if self.game.settings.required_role_id and not self.game.settings.test_mode:
                role = interaction.guild.get_role(int(self.game.settings.required_role_id))
                if not role:
                    await interaction.response.send_message(
                        "必要なロールが設定されていますが、見つかりませんでした。",
                        ephemeral=True
                    )
                    return
                if role not in interaction.user.roles:
                    await interaction.response.send_message(
                        f"{role.name}ロールが必要です。",
                        ephemeral=True
                    )
                    return

            if self.game.add_player(user_id):
                await interaction.response.send_message(
                    "バトルに参加しました！",
                    ephemeral=True
                )
                await self.update_battle_info(interaction)
            else:
                await interaction.response.send_message("すでに参加しています。", ephemeral=True)

        except Exception as e:
            print(f"Error in join_button: {e}")
            await interaction.response.send_message(
                "参加処理中にエラーが発生しました。",
                ephemeral=True
            )

    async def update_battle_info(self, interaction: discord.Interaction):
        """バトル情報を更新"""
        try:
            embed = await self._create_battle_info_embed()
            await interaction.message.edit(embed=embed, view=self)
        except Exception as e:
            print(f"Error updating battle info: {e}")

    async def _create_battle_info_embed(self) -> discord.Embed:
        """バトル情報のEmbed作成"""
        embed = discord.Embed(
            title="🏆 バトルロイヤル" + (" [🧪 テストモード]" if self.game.settings.test_mode else ""),
            description=self._get_battle_description(),
            color=discord.Color.blue()
        )
        
        participants_count = len(self.game.players)
        embed.add_field(
            name="参加状況",
            value=f"現在 {participants_count}人 が参加中"
        )
        
        if self.game.settings.test_mode:
            embed.add_field(
                name="⚠️ テストモード情報",
                value=f"ダミープレイヤー数: {self.game.settings.dummy_count}\n"
                      "ポイント・ロール付与: 無効",
                inline=False
            )
        
        return embed

    def _get_battle_description(self) -> str:
        """バトルの説明文を取得"""
        if self.game.status == BattleStatus.WAITING:
            return (f"下の「参加」ボタンをクリックして参加してください。\n"
                   f"{self.game.settings.start_delay_minutes}分後に開始します！")
        return "バトル進行中"

class BattleRoyale(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}
        print("Battle Royale cog initialized")

    async def get_battle_settings(self, guild_id: str):
        """バトル設定を取得"""
        try:
            settings = await self.bot.get_server_settings(guild_id)
            if not settings or not settings.global_settings.features_enabled.get('battle', True):
                return None
            return settings.battle_settings
        except Exception as e:
            print(f"Error getting battle settings: {e}")
            return None

    @app_commands.command(name="battle", description="バトルロイヤルを開始します")
    @app_commands.describe(
        test_mode="テストモードの有効化",
        dummy_count="テストモード時のダミープレイヤー数"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def start_battle(
        self,
        interaction: discord.Interaction,
        test_mode: bool = False,
        dummy_count: int = 10
    ):
        try:
            server_id = str(interaction.guild_id)
            
            if server_id in self.active_games:
                await interaction.response.send_message(
                    "すでにバトルが進行中です。",
                    ephemeral=True
                )
                return

            # 設定を取得
            settings = await self.get_battle_settings(server_id)
            if settings is None:
                await interaction.response.send_message(
                    "このサーバーではバトル機能が無効になっています。",
                    ephemeral=True
                )
                return

            # テストモードの設定を更新
            settings.test_mode = test_mode
            if test_mode:
                if dummy_count < 1 or dummy_count > 50:
                    await interaction.response.send_message(
                        "ダミープレイヤー数は1から50の間で設定してください。",
                        ephemeral=True
                    )
                    return
                settings.dummy_count = dummy_count

            # ゲームを初期化
            game = BattleGame(
                server_id=server_id,
                settings=settings,
                status=BattleStatus.WAITING,
                players=[],
                alive_players=[],
                dead_players=[],
                kill_counts={},
                revival_counts={},
                start_time=datetime.now(),
                round_number=1
            )

            if test_mode:
                # ダミープレイヤーを追加
                for i in range(dummy_count):
                    dummy_id = f"dummy_{i+1}"
                    game.add_player(dummy_id)
                
                # デバッグ情報を送信
                await interaction.channel.send(
                    embed=discord.Embed(
                        title="🧪 テストモード デバッグ情報",
                        description=f"ダミープレイヤーを {dummy_count}人 追加しました。\n"
                                  f"ダミーID: {', '.join(game.players[-dummy_count:])}",
                        color=discord.Color.greyple()
                    )
                )
            
            self.active_games[server_id] = game
            view = BattleView(game, self)
            
            # 初期Embedを作成
            initial_embed = await view._create_battle_info_embed()
            
            await interaction.response.send_message(embed=initial_embed, view=view)
            await self.start_countdown(interaction.channel, game)

        except Exception as e:
            print(f"Error starting battle: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message(
                "バトルの開始に失敗しました。",
                ephemeral=True
            )

    async def start_countdown(self, channel: discord.TextChannel, game: BattleGame):
        """カウントダウンを開始"""
        try:
            total_seconds = game.settings.start_delay_minutes * 60
            warning_times = [60, 30, 15]  # 警告を出すタイミング（秒）
            
            for remaining in range(total_seconds, 0, -1):
                if remaining in warning_times:
                    await channel.send(f"⚔️ 開始まであと{remaining}秒！")
                await asyncio.sleep(1)
            
            if game.status == BattleStatus.WAITING:
                if len(game.players) >= 4 or game.settings.test_mode:
                    game.status = BattleStatus.IN_PROGRESS
                    await self.start_battle_game(channel, game)
                else:
                    await channel.send("❌ 参加者が不足しているため、バトルを開始できません。")
                    del self.active_games[game.server_id]

        except Exception as e:
            print(f"Error in countdown: {e}")
            print(traceback.format_exc())
            await channel.send("エラーが発生したため、バトルを中止します。")
            if game.server_id in self.active_games:
                del self.active_games[game.server_id]

    async def start_battle_game(self, channel: discord.TextChannel, game: BattleGame):
        """バトルを開始"""
        try:
            start_embed = discord.Embed(
                title="⚔️ バトルロイヤル開始！" + (" [🧪 テストモード]" if game.settings.test_mode else ""),
                description=f"参加者数: {len(game.players)}人",
                color=discord.Color.green()
            )
            
            if game.settings.test_mode:
                start_embed.add_field(
                    name="🧪 テストモード情報",
                    value=f"実プレイヤー: {len([p for p in game.players if not p.startswith('dummy_')])}人\n"
                          f"ダミー: {len([p for p in game.players if p.startswith('dummy_')])}人",
                    inline=False
                )
            
            await channel.send(embed=start_embed)
            await self.run_battle_rounds(channel, game)

        except Exception as e:
            print(f"Error in battle game: {e}")
            print(traceback.format_exc())
            await channel.send("エラーが発生したため、バトルを中止します。")
            if game.server_id in self.active_games:
                del self.active_games[game.server_id]

    async def run_battle_rounds(self, channel: discord.TextChannel, game: BattleGame):
        """バトルのラウンドを実行"""
        try:
            while not game.is_finished:
                events = []
                for _ in range(min(len(game.alive_players) // 2, 5)):
                    event = generate_battle_event(game)
                    if event:
                        events.append(event)
                        await self.process_battle_event(game, event)

                round_embed = format_round_message(game.round_number, events, len(game.alive_players))
                if game.settings.test_mode:
                    round_embed.title = f"🧪 {round_embed.title}"

                await channel.send(embed=round_embed)
                
                if game.settings.test_mode:
                    await self.send_debug_info(channel, game)
                
                game.round_number += 1
                await asyncio.sleep(5)

            await self.end_battle(channel, game)
            
        except Exception as e:
            print(f"Error in battle rounds: {e}")
            print(traceback.format_exc())
            await channel.send("バトル進行中にエラーが発生しました。")
            await self.end_battle(channel, game)

    async def process_battle_event(self, game: BattleGame, event):
        """バトルイベントの処理"""
        if event.event_type == EventType.KILL:
            for player_id in event.killed_players:
                game.kill_player(player_id)
        elif event.event_type == EventType.REVIVE:
            for player_id in event.revived_players:
                game.revive_player(player_id)

    async def send_debug_info(self, channel: discord.TextChannel, game: BattleGame):
        """デバッグ情報の送信"""
        debug_embed = discord.Embed(
            title="🧪 ラウンドデバッグ情報",
            description=f"ラウンド {game.round_number}",
            color=discord.Color.greyple()
        )
        debug_embed.add_field(
            name="生存者情報",
            value=f"生存: {len(game.alive_players)}人\n死亡: {len(game.dead_players)}人"
        )
        await channel.send(embed=debug_embed)

    async def end_battle(self, channel: discord.TextChannel, game: BattleGame):
        """バトルを終了"""
        try:
            results = game.get_results()
            winner_id = results.winner
            
            embed = await self._create_results_embed(game, results)
            await channel.send(embed=embed)
            
            if not game.settings.test_mode and winner_id:
                await self.handle_rewards(channel.guild, winner_id, game)
            
        except Exception as e:
            print(f"Error in end battle: {e}")
            print(traceback.format_exc())
            await channel.send("バトル終了処理中にエラーが発生しました。")
        
        finally:
            if game.server_id in self.active_games:
                del self.active_games[game.server_id]

    async def _create_results_embed(self, game: BattleGame, results) -> discord.Embed:
        """結果表示用Embedの作成"""
        embed = discord.Embed(
            title="🏆 バトルロイヤル終了！" + (" [🧪 テストモード]" if game.settings.test_mode else ""),
            color=discord.Color.gold()
        )

        winner_id = results.winner
        if winner_id:
            embed.add_field(
                name="勝者",
                value=self._format_player_mention(winner_id, game.settings.test_mode),
                inline=False
            )

        if game.settings.test_mode:
            embed.add_field(
                name="⚠️ テストモード情報",
                value="このバトルはテストモードで実行されたため、\nポイントやロールの付与は行われません。",
                inline=False
            )

        return embed

    def _format_player_mention(self, player_id: str, is_test_mode: bool) -> str:
        """プレイヤーのメンション形式を返す"""
        if is_test_mode and player_id.startswith('dummy_'):
            return f"ダミープレイヤー {player_id}"
        return f"<@{player_id}>"

    async def handle_rewards(self, guild: discord.Guild, winner_id: str, game: BattleGame):
        """報酬の付与処理"""
        try:
            # 勝者ロールの付与
            if game.settings.winner_role_id:
                try:
                    winner = guild.get_member(int(winner_id))
                    role = guild.get_role(int(game.settings.winner_role_id))
                    if winner and role:
                        await winner.add_roles(role)
                except Exception as e:
                    print(f"Failed to add winner role: {e}")

            # ポイントの付与
            if game.settings.points_enabled and hasattr(self.bot, 'point_manager'):
                try:
                    # 優勝者の現在のポイントを取得
                    winner_current_points = await self.bot.point_manager.get_points(
                        game.server_id,
                        winner_id
                    )
                    
                    # 優勝ポイントを加算
                    winner_new_points = winner_current_points + game.settings.winner_points
                    await self.bot.point_manager.update_points(
                        winner_id,
                        game.server_id,
                        winner_new_points,
                        PointSource.BATTLE_WIN
                    )
                    
                    # キルポイントの付与
                    for player_id, kills in game.kill_counts.items():
                        if kills > 0:
                            # 現在のポイントを取得
                            current_points = await self.bot.point_manager.get_points(
                                game.server_id,
                                player_id
                            )
                            
                            # キルポイントを加算
                            kill_points = kills * game.settings.points_per_kill
                            new_points = current_points + kill_points
                            
                            await self.bot.point_manager.update_points(
                                player_id,
                                game.server_id,
                                new_points,
                                PointSource.BATTLE_KILL
                            )

                except Exception as e:
                    print(f"Failed to add points: {e}")
                    print(traceback.format_exc())

        except Exception as e:
            print(f"Error handling rewards: {e}")
            print(traceback.format_exc())

async def setup(bot):
    print("[Battle] Setting up Battle Royale Cog")
    try:
        await bot.add_cog(BattleRoyale(bot))
        print("[Battle] Successfully added Battle Royale Cog")
    except Exception as e:
        print(f"[Battle] Failed to add cog: {e}")
        print(traceback.format_exc())