import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime
import traceback
from typing import Optional, Dict

from models.battle import BattleGame, BattleStatus, BattleSettings, BattleEvent, EventType
from utils.battle_events import generate_battle_event, format_round_message

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
        if self.game.settings.required_role_id and not self.game.settings.test_mode:
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
            title="🏆 バトルロイヤル" + (" [🧪 テストモード]" if self.game.settings.test_mode else ""),
            description=f"下の「参加」ボタンをクリックして参加してください。\n{self.game.settings.start_delay_minutes}分後に開始します！" if self.game.status == BattleStatus.WAITING else "バトル進行中",
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
                value=f"ダミープレイヤー数: {self.game.settings.dummy_count}\nポイント・ロール付与: 無効",
                inline=False
            )
        
        await interaction.message.edit(embed=embed, view=self)

class BattleRoyale(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}
        print("Battle Royale cog initialized")

    @app_commands.command(name="battle", description="バトルロイヤルを開始します")
    @app_commands.describe(
        required_role="参加に必要なロール（オプション）",
        winner_role="勝者に付与するロール（オプション）",
        points_enabled="ポイント付与システムの有効/無効",
        points_per_kill="1キルあたりのポイント",
        winner_points="優勝賞金",
        start_delay="開始までの待機時間（分）",
        test_mode="テストモードの有効化",
        dummy_count="テストモード時のダミープレイヤー数"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def start_battle(
        self,
        interaction: discord.Interaction,
        required_role: Optional[discord.Role] = None,
        winner_role: Optional[discord.Role] = None,
        points_enabled: bool = True,
        points_per_kill: int = 100,
        winner_points: int = 1000,
        start_delay: int = 2,
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

            if start_delay < 1 or start_delay > 10:
                await interaction.response.send_message(
                    "待機時間は1分から10分の間で設定してください。",
                    ephemeral=True
                )
                return

            if test_mode and (dummy_count < 1 or dummy_count > 50):
                await interaction.response.send_message(
                    "ダミープレイヤー数は1から50の間で設定してください。",
                    ephemeral=True
                )
                return

            settings = BattleSettings(
                required_role_id=str(required_role.id) if required_role else None,
                winner_role_id=str(winner_role.id) if winner_role else None,
                points_enabled=points_enabled,
                points_per_kill=points_per_kill,
                winner_points=winner_points,
                start_delay_minutes=start_delay,
                test_mode=test_mode,
                dummy_count=dummy_count
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
                start_time=datetime.now(),
                round_number=1
            )

            if test_mode:
                # ダミープレイヤーを追加
                for i in range(dummy_count):
                    dummy_id = f"dummy_{i+1}"
                    game.add_player(dummy_id)
                # デバッグメッセージを送信
                await interaction.channel.send(
                    embed=discord.Embed(
                        title="🧪 テストモード デバッグ情報",
                        description=f"ダミープレイヤーを {dummy_count}人 追加しました。\nダミーID: {', '.join(game.players[-dummy_count:])}",
                        color=discord.Color.greyple()
                    )
                )
            
            self.active_games[server_id] = game
            view = BattleView(game, self)
            
            initial_embed = discord.Embed(
                title="🏆 バトルロイヤル" + (" [🧪 テストモード]" if test_mode else ""),
                description=f"下の「参加」ボタンをクリックして参加してください。\n{start_delay}分後に開始します！",
                color=discord.Color.blue()
            )
            initial_embed.add_field(
                name="参加状況",
                value=f"現在 {dummy_count if test_mode else 0}人 が参加中"
            )

            if test_mode:
                initial_embed.add_field(
                    name="⚠️ テストモード情報",
                    value="このバトルはテストモードで実行されます。\nポイントやロールの付与は行われません。",
                    inline=False
                )

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
                debug_embed = discord.Embed(
                    title="🧪 テストモード デバッグ情報",
                    description="バトル開始時の状態",
                    color=discord.Color.greyple()
                )
                debug_embed.add_field(
                    name="参加者内訳",
                    value=f"実プレイヤー: {len([p for p in game.players if not p.startswith('dummy_')])}人\nダミー: {len([p for p in game.players if p.startswith('dummy_')])}人"
                )
                await channel.send(embed=debug_embed)
            
            await channel.send(embed=start_embed)

            while not game.is_finished:
                events = []
                for _ in range(min(len(game.alive_players) // 2, 5)):
                    event = generate_battle_event(game.alive_players, game.dead_players)
                    if event:
                        events.append(event)
                        if event.killed_players:
                            for player_id in event.killed_players:
                                game.kill_player(player_id)
                        if event.revived_players:
                            for player_id in event.revived_players:
                                game.revive_player(player_id)

                round_embed = format_round_message(game.round_number, events, len(game.alive_players))

                if game.settings.test_mode:
                    round_embed.title = f"🧪 {round_embed.title}"

                await channel.send(embed=round_embed)

                if game.settings.test_mode:
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
                
                game.round_number += 1
                await asyncio.sleep(5)

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
            
            embed = discord.Embed(
                title="🏆 バトルロイヤル終了！" + (" [🧪 テストモード]" if game.settings.test_mode else ""),
                color=discord.Color.gold()
            )

            if winner_id:
                embed.add_field(
                    name="勝者",
                    value=f"<@{winner_id}>" if not game.settings.test_mode or not winner_id.startswith("dummy_") else f"ダミープレイヤー {winner_id}",
                    inline=False
                )

                if not game.settings.test_mode:
                    # 通常モードの場合のみロールとポイントを付与
                    if game.settings.winner_role_id:
                        try:
                            winner = channel.guild.get_member(int(winner_id))
                            role = channel.guild.get_role(int(game.settings.winner_role_id))
                            if winner and role:
                                await winner.add_roles(role)
                        except Exception as e:
                            print(f"Failed to add winner role: {e}")

                    if game.settings.points_enabled and hasattr(self.bot, 'db'):
                        try:
                            self.bot.db.add_points(winner_id, game.settings.winner_points)
                            for player_id, kills in game.kill_counts.items():
                                if kills > 0:
                                    kill_points = kills * game.settings.points_per_kill
                                    self.bot.db.add_points(player_id, kill_points)
                        except Exception as e:
                            print(f"Failed to add points: {e}")

            # # 上位入賞者を表示
            # runners_up_text = []
            # for i, player_id in enumerate(results.runners_up):
            #     if game.settings.test_mode and player_id.startswith("dummy_"):
            #         runners_up_text.append(f"{i+2}位: ダミープレイヤー {player_id}")
            #     else:
            #         runners_up_text.append(f"{i+2}位: <@{player_id}>")
            
            # runners_up = "\n".join(runners_up_text)
            # embed.add_field(name="入賞者", value=runners_up if runners_up else "なし", inline=False)

            # # キル数ランキング
            # kill_ranking = sorted(
            #     [(player_id, kills) for player_id, kills in results.kill_counts.items() if kills > 0],
            #     key=lambda x: x[1],
            #     reverse=True
            # )[:5]
            # if kill_ranking:
            #     kill_text = []
            #     for player_id, kills in kill_ranking:
            #         if game.settings.test_mode and player_id.startswith("dummy_"):
            #             kill_text.append(f"ダミープレイヤー {player_id}: {kills}キル")
            #         else:
            #             kill_text.append(f"<@{player_id}>: {kills}キル")
            #     embed.add_field(
            #         name="キル数ランキング",
            #         value="\n".join(kill_text),
            #         inline=False
            #     )

            if game.settings.test_mode:
                embed.add_field(
                    name="⚠️ テストモード情報",
                    value="このバトルはテストモードで実行されたため、\nポイントやロールの付与は行われません。",
                    inline=False
                )

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