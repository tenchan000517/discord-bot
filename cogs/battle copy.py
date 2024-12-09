import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime
import traceback
from typing import Optional, Dict

from models.battle import BattleGame, BattleStatus, BattleSettings
from utils.battle_events import generate_battle_event, format_round_message

class BattleSettings:
    def __init__(
        self,
        required_role_id: Optional[str] = None,
        winner_role_id: Optional[str] = None,
        points_enabled: bool = True,
        points_per_kill: int = 100,
        winner_points: int = 1000,
        start_delay_minutes: int = 2  # 追加: 開始までの待機時間（分）
    ):
        self.required_role_id = required_role_id
        self.winner_role_id = winner_role_id
        self.points_enabled = points_enabled
        self.points_per_kill = points_per_kill
        self.winner_points = winner_points
        self.start_delay_minutes = start_delay_minutes

class BattleView(discord.ui.View):
    def __init__(self, game: BattleGame, cog):
        super().__init__(timeout=None)
        self.game = game
        self.cog = cog

    @discord.ui.button(label="参加", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """バトルに参加"""
        if self.game.status != BattleStatus.WAITING:
            await interaction.response.send_message("現在参加を受け付けていません。", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        if self.game.settings.required_role_id:
            role = interaction.guild.get_role(int(self.game.settings.required_role_id))
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

    async def update_battle_info(self, interaction: discord.Interaction):
        """バトル情報を更新"""
        embed = discord.Embed(
            title="🏆 バトルロイヤル",
            description=f"下の「参加」ボタンをクリックして参加してください。\n{self.game.settings.start_delay_minutes}分後に開始します！" if self.game.status == BattleStatus.WAITING else "バトル進行中",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="参加状況", 
            value=f"現在 {len(self.game.players)}人 が参加中"
        )
        
        await interaction.message.edit(embed=embed, view=self)

class BattleRoyale(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # active_gamesをディクショナリとして初期化
        print("Battle Royale cog initialized")

    @app_commands.command(name="battle", description="バトルロイヤルを開始します")
    @app_commands.describe(
        required_role="参加に必要なロール（オプション）",
        winner_role="勝者に付与するロール（オプション）",
        points_enabled="ポイント付与システムの有効/無効",
        points_per_kill="1キルあたりのポイント",
        winner_points="優勝賞金",
        start_delay="開始までの待機時間（分）"  # 追加: 待機時間のパラメータ
    )
    @app_commands.checks.has_permissions(administrator=True) # 管理者だけでなくMODなども使用できるようにしたい
    async def start_battle(
        self,
        interaction: discord.Interaction,
        required_role: Optional[discord.Role] = None,
        winner_role: Optional[discord.Role] = None,
        points_enabled: bool = True,
        points_per_kill: int = 100,
        winner_points: int = 1000,
        start_delay: int = 2  # デフォルト2分
    ):
        try:
            server_id = str(interaction.guild_id)
            
            if server_id in self.active_games:
                await interaction.response.send_message(
                    "すでにバトルが進行中です。",
                    ephemeral=True
                )
                return

            # 待機時間の検証
            if start_delay < 1 or start_delay > 10:
                await interaction.response.send_message(
                    "待機時間は1分から10分の間で設定してください。",
                    ephemeral=True
                )
                return

            settings = BattleSettings(
                required_role_id=str(required_role.id) if required_role else None,
                winner_role_id=str(winner_role.id) if winner_role else None,
                points_enabled=points_enabled,
                points_per_kill=points_per_kill,
                winner_points=winner_points,
                start_delay_minutes=start_delay  # 待機時間を設定
            )

            game = BattleGame(
                server_id=server_id,
                status=BattleStatus.WAITING,
                settings=settings,
                players=[],
                alive_players=[],
                dead_players=[],
                kill_counts={},
                revival_counts={},
                start_time=datetime.now()
            )
            
            self.active_games[server_id] = game
            view = BattleView(game, self)
            
            initial_embed = discord.Embed(
                title="🏆 バトルロイヤル",
                description=f"下の絵文字をクリックして参加してください。\n{start_delay}分後に開始します！",
                color=discord.Color.blue()
            )
            initial_embed.add_field(name="参加状況", value="現在 0人 が参加中")

            await interaction.response.send_message(embed=initial_embed, view=view)
            await self.start_countdown(interaction.channel, game)

        except Exception as e:
            print(f"Error starting battle: {e}")
            print(traceback.format_exc())
            await interaction.response.send_message("バトルの開始に失敗しました。", ephemeral=True)

    async def start_countdown(self, channel: discord.TextChannel, game: BattleGame):
        """カウントダウンを開始"""
        try:
            total_seconds = game.settings.start_delay_minutes * 60
            warning_times = [60, 30, 15]  # 警告を出すタイミング（秒）
            
            # メインの待機時間
            for remaining in range(total_seconds, 0, -1):
                if remaining in warning_times:
                    await channel.send(f"⚔️ 開始まであと{remaining}秒！")
                await asyncio.sleep(1)
            
            if game.status == BattleStatus.WAITING:
                if len(game.players) >= 4:
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
            await channel.send(
                embed=discord.Embed(
                    title="⚔️ バトルロイヤル開始！",
                    description=f"参加者数: {len(game.players)}人",
                    color=discord.Color.green()
                )
            )

            # メインゲームループ
            while not game.is_finished:
                # 各ラウンドでイベントを生成
                events = []
                for _ in range(min(len(game.alive_players) // 2, 5)):  # 1ラウンドあたり最大5イベント
                    event = generate_battle_event(game.alive_players, game.dead_players)
                    if event:
                        events.append(event)
                        # イベントの結果を反映
                        if event.killed_players:
                            for player_id in event.killed_players:
                                game.kill_player(player_id)
                        if event.revived_players:
                            for player_id in event.revived_players:
                                game.revive_player(player_id)

                # ラウンドメッセージを送信
                round_message = format_round_message(game.round_number, events, len(game.alive_players))
                await channel.send(round_message)
                
                game.round_number += 1
                await asyncio.sleep(5)  # ラウンド間の待機時間

            # ゲーム終了処理
            await self.end_battle(channel, game)
            
        except Exception as e:
            print(f"Error in battle game: {e}")
            print(traceback.format_exc())
            await channel.send("エラーが発生したため、バトルを中止します。")
            if game.server_id in self.active_games:
                del self.active_games[game.server_id]

    async def end_battle(self, channel: discord.TextChannel, game: BattleGame):
        """バトルを終了"""
        try:
            results = game.get_results()
            winner_id = results.winner
            
            # 結果を表示
            embed = discord.Embed(
                title="🏆 バトルロイヤル終了！",
                color=discord.Color.gold()
            )

            if winner_id:
                embed.add_field(
                    name="勝者",
                    value=f"<@{winner_id}>",
                    inline=False
                )

                # 勝者にロールを付与
                if game.settings.winner_role_id:
                    try:
                        winner = channel.guild.get_member(int(winner_id))
                        role = channel.guild.get_role(int(game.settings.winner_role_id))
                        if winner and role:
                            await winner.add_roles(role)
                    except Exception as e:
                        print(f"Failed to add winner role: {e}")

                # ポイントを付与
                if game.settings.points_enabled and hasattr(self.bot, 'db'):
                    try:
                        # 勝者にポイントを付与
                        self.bot.db.add_points(winner_id, game.settings.winner_points)
                        
                        # キルポイントを付与
                        for player_id, kills in game.kill_counts.items():
                            if kills > 0:
                                kill_points = kills * game.settings.points_per_kill
                                self.bot.db.add_points(player_id, kill_points)
                    except Exception as e:
                        print(f"Failed to add points: {e}")

            # 上位入賞者を表示
            runners_up = "\n".join([f"{i+2}位: <@{player_id}>" for i, player_id in enumerate(results.runners_up)])
            embed.add_field(name="入賞者", value=runners_up if runners_up else "なし", inline=False)

            # キル数ランキング
            kill_ranking = sorted(
                [(player_id, kills) for player_id, kills in results.kill_counts.items() if kills > 0],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            if kill_ranking:
                kill_text = "\n".join([f"<@{player_id}>: {kills}キル" for player_id, kills in kill_ranking])
                embed.add_field(name="キル数ランキング", value=kill_text, inline=False)

            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error in end battle: {e}")
            print(traceback.format_exc())
            await channel.send("バトル終了処理中にエラーが発生しました。")
        
        finally:
            # ゲームを削除
            if game.server_id in self.active_games:
                del self.active_games[game.server_id]

async def setup(bot):
    print("[Battle] Setting up Battle Royale Cog")
    try:
        await bot.add_cog(BattleRoyale(bot))
        print("[Battle] Successfully added Battle Royale Cog")
    except Exception as e:
        print(f"[Battle] Failed to add cog: {e}")
        print(traceback.format_exc())